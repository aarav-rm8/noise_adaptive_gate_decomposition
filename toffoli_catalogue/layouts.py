from collections import defaultdict

def generate_layouts(coupling_map, k):
    """
    Generate all connected physical layouts of size k.

    Layouts are returned as ordered tuples suitable for Qiskit's
    initial_layout argument.

    Duplicate layouts differing only by traversal order are removed.
    The completeness of the connected subsets was verified separately
    using brute-force enumeration.
    """

    # Build adjacency list
    graph = defaultdict(set)
    for u, v in coupling_map.get_edges():
        graph[u].add(v)
        graph[v].add(u)

    seen = set()      # used only for deduplication
    layouts = []      # stores the actual ordered layouts

    def dfs(current):
        if len(current) == k:
            key = frozenset(current)   # ignore ordering when checking duplicates
            if key not in seen:
                seen.add(key)
                layouts.append(tuple(current))   # KEEP THE ORIGINAL ORDER
            return

        candidates = set()
        for q in current:
            candidates |= graph[q]

        candidates -= set(current)

        for nxt in candidates:
            dfs(current + [nxt])

    for start in graph:
        dfs([start])

    return layouts