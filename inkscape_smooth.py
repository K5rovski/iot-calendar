import svgpathtools as svg
from typing import List, Tuple

def points(path: svg.Path):
    for seg in path:
        yield seg.start
    yield path.end

def normalized(x: complex) -> complex:
    return x / abs(x)

def autosmooth_handles(a: complex, b: complex, c: complex, alpha=1/3) -> Tuple[complex, complex]:
    """
    Computes the autosmooth handles for point `b` with `a` previuos and `c` next
    """
    v_next = c - b
    v_prev = a - b

    l_next = abs(v_next)
    l_prev = abs(v_prev)

    u = normalized((l_prev / l_next) * v_next - v_prev)
    return (
        -u * (alpha * l_prev),
         u * (alpha * l_next),
    )

def autosmooth(points: List[complex], alpha=1/3) -> svg.Path:
    """
    Create a series of cubic bezier curves that pass smoothly through `points`
    This is the same method used in inkscape with auto-smooth node types
    Handles are oriented perpindicular to the angle bisector between prev, cur, next points
    Handles are alpha=1/3 the length of the distance between prev & cur (and cur & next respectively)
    """
    # the calculations are a bit annoying because inkscape is node-centric and svgpathtools is segment-centric

    if len(points) <= 2:
        raise ValueError('Need more than 2 points')

    ret = svg.Path()

    # initialize segments
    for i in range(len(points) - 1):
        ret.append(svg.CubicBezier(points[i], points[i], points[i + 1], points[i + 1]))

    for i in range(1, len(points) - 1):
        u, v = autosmooth_handles(*points[i-1:i+2], alpha=alpha)
        ret[i - 1].control2 += u
        ret[i    ].control1 += v

    # handle closed shape
    if points[0] == points[-1]:
        u, v = autosmooth_handles(points[-2], points[0], points[1])
        ret[-1].control2 += u
        ret[0 ].control1 += v

    return ret

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--alpha', type=float, default=1/3)
    args = parser.parse_args()

    paths, _ = svg.svg2paths(args.input)

    paths_out = [autosmooth(list(points(path)), alpha=args.alpha).translated(10j) for path in paths]

    svg.wsvg(paths + paths_out, filename=args.output)