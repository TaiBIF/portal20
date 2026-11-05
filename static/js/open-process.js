(function () {
    'use strict';

    const root = document.querySelector('[data-open-process-flow]');
    if (!root) return;

    const svg = root.querySelector('svg');
    const connections = root.querySelector('[data-flow-connections]');
    const grid = root.querySelector('.open-process-flow-grid');
    const desktop = window.matchMedia('(min-width: 900px)');
    const arrowheadLength = Number(root.querySelector('marker').getAttribute('markerWidth'));
    const nodes = new Map(Array.from(root.querySelectorAll('[data-flow-node]'), function (node) {
        return [node.dataset.flowNode, node];
    }));

    // Each entry draws one arrow. The first two arrows use separate lanes.
    const edges = [
        { from: 'prepare', to: 'validate', lane: -10 },
        { from: 'validate', to: 'prepare', lane: 10 },
        { from: 'validate', to: 'upload' },
        { from: 'upload', to: 'license' },
        { from: 'license', to: 'publish' },
        { from: 'publish', to: 'reuse' },
        { from: 'reuse', to: 'prepare', cycle: true }
    ];

    function roundedPath(points) {
        let path = 'M ' + points[0].join(' ');
        for (let i = 1; i < points.length - 1; i += 1) {
            const previous = points[i - 1];
            const current = points[i];
            const next = points[i + 1];
            const incoming = Math.hypot(current[0] - previous[0], current[1] - previous[1]);
            const outgoing = Math.hypot(next[0] - current[0], next[1] - current[1]);
            const radius = Math.min(10, incoming / 2, outgoing / 2);
            const before = current.map(function (value, axis) {
                return value + (previous[axis] - value) * radius / incoming;
            });
            const after = current.map(function (value, axis) {
                return value + (next[axis] - value) * radius / outgoing;
            });
            path += ' L ' + before.join(' ') + ' Q ' + current.join(' ') + ' ' + after.join(' ');
        }
        return path + ' L ' + points[points.length - 1].join(' ');
    }

    function arrowPoints(from, to, edge) {
        const gap = 5;
        const lane = edge.lane || 0;
        if (edge.cycle && !desktop.matches) {
            // The mobile return path runs in the reserved left gutter.
            return [[from.left - gap, from.cy], [12, from.cy], [12, to.cy], [to.left - gap, to.cy]];
        }
        if (Math.abs(from.cy - to.cy) < 1) {
            const rightward = to.cx > from.cx;
            return [
                [rightward ? from.right + gap : from.left - gap, from.cy + lane],
                [rightward ? to.left - gap : to.right + gap, to.cy + lane]
            ];
        }
        const downward = to.cy > from.cy;
        return [
            [from.cx + lane, downward ? from.bottom + gap : from.top - gap],
            [to.cx + lane, downward ? to.top - gap : to.bottom + gap]
        ];
    }

    function draw() {
        const bounds = root.getBoundingClientRect();
        if (!bounds.width || !bounds.height) return;
        svg.setAttribute('viewBox', '0 0 ' + bounds.width + ' ' + bounds.height);
        const boxes = new Map();
        nodes.forEach(function (node, id) {
            const box = node.getBoundingClientRect();
            boxes.set(id, {
                left: box.left - bounds.left,
                right: box.right - bounds.left,
                top: box.top - bounds.top,
                bottom: box.bottom - bounds.top,
                cx: box.left - bounds.left + box.width / 2,
                cy: box.top - bounds.top + box.height / 2
            });
        });
        const fragment = document.createDocumentFragment();
        edges.forEach(function (edge) {
            const from = boxes.get(edge.from);
            const to = boxes.get(edge.to);
            if (!from || !to) return;
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('class', 'open-process-flow-connection');
            path.setAttribute('data-from', edge.from);
            path.setAttribute('data-to', edge.to);
            const points = arrowPoints(from, to, edge);
            const tip = points[points.length - 1];
            const previous = points[points.length - 2];
            const length = Math.hypot(tip[0] - previous[0], tip[1] - previous[1]);
            // Stop the shaft at the arrowhead's base, keeping its tip at the target.
            points[points.length - 1] = tip.map(function (value, axis) {
                return value - (value - previous[axis]) * arrowheadLength / length;
            });
            path.setAttribute('d', roundedPath(points));
            fragment.appendChild(path);
        });
        connections.replaceChildren(fragment);
    }

    let frame;
    function scheduleDraw() {
        if (frame) cancelAnimationFrame(frame);
        frame = requestAnimationFrame(function () {
            frame = null;
            draw();
        });
    }

    if ('ResizeObserver' in window) {
        const observer = new ResizeObserver(scheduleDraw);
        observer.observe(root);
        observer.observe(grid);
        nodes.forEach(function (node) { observer.observe(node); });
    }
    window.addEventListener('resize', scheduleDraw);
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(scheduleDraw);
    }
    scheduleDraw();
})();
