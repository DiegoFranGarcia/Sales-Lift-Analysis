import { useEffect, useRef } from "react";

/**
 * Render an Observable Plot figure into a div.
 * `build` receives the measured pixel width so plots can be responsive.
 */
export function usePlot(build, deps = []) {
  const ref = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let node;
    const draw = () => {
      const width = el.clientWidth || 900;
      node?.remove();
      node = build(width);
      if (node) el.append(node);
    };

    draw();
    const ro = new ResizeObserver(draw);
    ro.observe(el);
    return () => { ro.disconnect(); node?.remove(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return ref;
}