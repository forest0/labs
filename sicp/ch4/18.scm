(lambda ⟨vars⟩
  (define u ⟨e1⟩)
  (define v ⟨e2⟩)
  ⟨e3⟩)

; T1
; transform in the text
(lambda ⟨vars⟩
  (let ((u '*unassigned*)
        (v '*unassigned*))
    (set! u ⟨e1⟩)
    (set! v ⟨e2⟩)
    ⟨e3⟩))

; T2
; new transform
(lambda ⟨vars⟩
  (let ((u '*unassigned*) (v '*unassigned*))
    (let ((a ⟨e1⟩) (b ⟨e2⟩))
      (set! u a)
      (set! v b))
    ⟨e3⟩))

; target
; in the bootstrap, dy depends on y
(define (solve f y0 dt)
  (define y (integral (delay dy) y0 dt))
  (define dy (stream-map f y))
  y)

; target transformed by T1
; this version will work
(lambda (f y0 dt)
  (let ((y '*unassigned*)
        (dy '*unassigned*))
    (set! y (integral (delay dy) y0 dt))
    (set! dy (stream-map f y)) ; when evaluate here, y is already defined
    y))

; =========================

; target transformed by T2
; this version will not work
(lambda (f y0 dt)
  (let ((y '*unassigned*)
        (dy '*unassigned*))
    (let ((a (integral (delay dy) y0 dt))
          ; when evaluate here, y is still *unassigned*, b will fail
          (b (strem-map f y)))
      (set! y a)
      (set! dy b))
    ⟨e3⟩))

