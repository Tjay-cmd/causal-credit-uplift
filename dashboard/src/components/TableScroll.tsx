"use client";

import {
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
  useCallback,
  useRef,
} from "react";

/**
 * Horizontal table scroller that works with touch swipe and mouse drag,
 * with a thicker always-visible scrollbar so the "slider" is usable.
 */
export function TableScroll({
  children,
  className = "",
  hint = "Swipe or drag sideways to see more columns",
}: {
  children: ReactNode;
  className?: string;
  hint?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const drag = useRef<{
    active: boolean;
    startX: number;
    startScroll: number;
    moved: boolean;
  }>({ active: false, startX: 0, startScroll: 0, moved: false });

  const onPointerDown = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    // Leave native touch scrolling alone; drag is for mouse / pen.
    if (e.pointerType === "touch") return;
    const el = ref.current;
    if (!el) return;
    drag.current = {
      active: true,
      startX: e.clientX,
      startScroll: el.scrollLeft,
      moved: false,
    };
    el.setPointerCapture(e.pointerId);
    el.classList.add("is-dragging");
  }, []);

  const onPointerMove = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    if (!drag.current.active || e.pointerType === "touch") return;
    const el = ref.current;
    if (!el) return;
    const dx = e.clientX - drag.current.startX;
    if (Math.abs(dx) > 3) drag.current.moved = true;
    el.scrollLeft = drag.current.startScroll - dx;
  }, []);

  const endDrag = useCallback((e: ReactPointerEvent<HTMLDivElement>) => {
    if (!drag.current.active) return;
    const el = ref.current;
    drag.current.active = false;
    el?.classList.remove("is-dragging");
    try {
      el?.releasePointerCapture(e.pointerId);
    } catch {
      /* already released */
    }
  }, []);

  return (
    <div className={`min-w-0 ${className}`}>
      <p className="mb-2 font-mono text-[10px] uppercase tracking-widest text-muted md:hidden">
        {hint}
      </p>
      <div
        ref={ref}
        className="table-scroll overflow-x-auto overscroll-x-contain rounded-lg border border-edge"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      >
        {children}
      </div>
    </div>
  );
}
