; the extra frame comes from the variable binding of the let.

; when evaluate e3, e1 and e2 are well defined in
; (enclosing-environment e3)

(lambda ⟨vars⟩
  (define u ⟨e1⟩)
  (define v ⟨e2⟩)
  ⟨e3⟩)

; transform version1
; this needs an extra frame
(lambda ⟨vars⟩
  (let ((u '*unassigned*)
        (v '*unassigned*))
    (set! u ⟨e1⟩)
    (set! v ⟨e2⟩)
    ⟨e3⟩))

; transform version2
; this does not need an extra frame
; idea: move u and v's bindings upward
;       to its enclosing environment.
(lambda ⟨vars u v⟩
  ⟨e3⟩)
