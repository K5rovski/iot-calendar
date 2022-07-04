#!/usr/bin/python

from PIL import Image
from PIL import ImageDraw
import math
from xml.dom.minidom import parse
import sys
from mpmath import mp

divisions = 2

mp.prec = 2000

class Polynomial:
	def __init__(self, poly):
		self.poly = tuple(map(mp.mpf, poly))
	
	def __call__(self, t):
		x = mp.mpf(1.0)
		ans = mp.mpf(0)
		for i in range(len(self.poly)):
			ans += x * self.poly[i]
			x *= t
		return ans
	
	def __len__(self):
		return len(self.poly)
	
	def __getitem__(self, idx):
		return self.poly[idx]
	
	def __set__(self, idx, val):
		self.poly[idx] = val
	
	def __mul__(self, o):
		if(type(o) in (int,  float)):
			return Polynomial([(o * self.poly[i]) for i in range(len(self.poly))])
		else:
			arr = [0] * (len(self.poly) + len(o) - 1)
		
			for i in range(len(self.poly)):
				for j in range(len(o)):
					arr[i+j] += self.poly[i] * o[j]
		
			return Polynomial(arr)
	
	def __pow__(self, o):
		arr = Polynomial([1])
		
		for i in range(o):
			arr *= self
		
		return arr
	
	def __rmul__(self, o):
		return self * o
	
	def __add__(self, o):
		if(type(o) in (int,  float)):
			arr = self.poly[::]
			arr[0] += o
			
			return Polynomial(arr)
		else:
			arr = [0] * max(len(self.poly), len(o))
		
			for i in range(len(self.poly)):
				arr[i] += self.poly[i]
			
			for j in range(len(o)):
				arr[j] += o[j]
		
			return Polynomial(arr)
	
	def __radd__(self, o):
		return self + o
	
	def __repr__(self):
		return " + ".join(["%.2fx^%d" % (self.poly[i], i) for i in range(len(self.poly)-1,-1,-1)])

class Bezier:
	def __init__(self, p):
		self.x = Polynomial([1,-1])**3 * p[0][0] + \
					3 * Polynomial([0, 1]) * Polynomial([1,-1])**2 * p[1][0] + \
					3 * Polynomial([0, 0, 1]) * Polynomial([1,-1]) * p[2][0] + \
					Polynomial([0, 0, 0, 1]) * p[3][0]
		self.y = Polynomial([1,-1])**3 * p[0][1] + \
					3 * Polynomial([0, 1]) * Polynomial([1,-1])**2 * p[1][1] + \
					3 * Polynomial([0, 0, 1]) * Polynomial([1,-1]) * p[2][1] + \
					Polynomial([0, 0, 0, 1]) * p[3][1]
	
	def __call__(self, t):
		return (self.x(t), self.y(t))

def add(a, b):
	return (a[0] + b[0], a[1] + b[1])

def multiply(a, b):
	return (a[0] * b, a[1] * b)

def divide(a, b):
	return (a[0] / b, a[1] / b)

w = 1024
h = 1024

dom = parse(sys.argv[1])

instructions = dom.getElementsByTagName('path')[0].attributes['d'].value.split(" ")

i = 0
P = (0,0)
path = []

while i < len(instructions):
	if instructions[i] == 'M':
		i += 1
		P = tuple(map(float, instructions[i].split(',')))
	elif instructions[i] == 'm':
		i += 1
		Pp = list(map(float, instructions[i].split(',')))
		P = (P[0] + Pp[0], P[1] + Pp[1])
	elif instructions[i] == 'C':
		i += 1
		while i<len(instructions) and not ('a' <= instructions[i][0] <= 'z' or 'A' <= instructions[i][0] <= 'Z'):
			path.append(Bezier((
				P,
				tuple(map(float, instructions[i].split(','))),
				tuple(map(float, instructions[i+1].split(','))),
				tuple(map(float, instructions[i+2].split(',')))
			)))
			P = tuple(map(float, instructions[i+2].split(',')))
			i += 3
		i -= 1
	elif instructions[i] == 'c':
		i += 1
		while i<len(instructions) and not ('a' <= instructions[i][0] <= 'z' or 'A' <= instructions[i][0] <= 'Z'):
			path.append(Bezier((
				P,
				add(P, tuple(map(float, instructions[i].split(',')))),
				add(P, tuple(map(float, instructions[i+1].split(',')))),
				add(P, tuple(map(float, instructions[i+2].split(','))))
			)))
			P = add(P, tuple(map(float, instructions[i+2].split(','))))
			i += 3
		i -= 1
	elif instructions[i] == 'z':
		pass
	else:
		print ('unknown instruction',instructions[i])
	i += 1

points = []
p = None
p0 = None

out = Image.new('RGB', (w, h))
draw = ImageDraw.Draw(out)
draw.rectangle((0, 0, w, h), fill="#ffffff")

for bez in path:
	for i in range(0, divisions):
		p2 = bez(i/float(divisions))
		if p:
			#draw.line(p + p2, fill='#ff0000')
			pass
		else:
			p0 = p2
		p = p2
		points.append(divide(p, 1000.0))

l = float(len(points))
points = points * 7
points = [(mp.mpf((i-3*l)/l),) + points[i] for i in range(len(points))]

#draw.line(p + p0, fill='#ff0000')

x = mp.matrix([[points[i][1]] for i in range(len(points))])
y = mp.matrix([[points[i][2]] for i in range(len(points))])
X = mp.matrix([[points[i][0]**j for j in range(len(points))] for i in range(len(points))])

sol = (X.T * X) ** -1 * X.T

x = Polynomial((sol * x).T)
y = Polynomial((sol * y).T)

p = None
p0 = None
for i in range(1000):
	p2 = (x(i / 1000.) * 1000, y(i / 1000.) * 1000)
	p2 = (max(0, min(1024, p2[0])),max(0, min(1024, p2[1])))
	
	if p:
		draw.line(p + p2, fill='#000000')
	else:
		p0 = p2
		
	p = p2

draw.line(p + p0, fill='#000000')
del draw

out.save('output.png')

f = open("polynomial.txt", "w")
f.write("x %d\n" % len(x))
for i in range(len(x)):
	f.write("%s\n" % str(x[i]))

f.write("y %d\n" % len(y))
for i in range(len(y)):
	f.write("%s\n" % str(y[i]))
f.close()