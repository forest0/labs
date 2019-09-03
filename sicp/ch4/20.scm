(define (letrec->let exp)
  (define (letrec-bindings exp)
    (cadr exp))
  (define (letrec-body exp)
    (cddr exp))
  (define (parameters exp)
    (map car (letrec-bindings exp)))
  (define (initial-arguments exp)
    (map cadr (letrec-bindings exp)))
  (define (declare-variables params)
    (map (lambda (v) (list v '*unassigned*))
         params))
  (define (set-variables bindings)
    (map (lambda (binding)
                   (cons 'set! binding))
                 bindings))
  (make-let
    (declare-variables (parameters exp))
    (make-begin
      (append (set-variables (letrec-bindings exp))
              (letrec-body exp)))))

(define (f x)
  (letrec
    ((even? (lambda (n)
              (if (= n 0) true (odd? (- n 1)))))
     (odd? (lambda (n)
             (if (= n 0) false (even? (- n 1))))))
    ⟨rest of body of f⟩))


; NOTE: answer from http://community.schemewiki.org/?sicp-ex-4.20,
; this flow chart is awesome, but may not be displayed correctly on html.
;
; Letrec Environment Diagram
; ==========================
; even? and odd? procs reference E2 because the are created when evaluating
; set! within the body of the lambda.  This means they can lookup the even?
; and odd? variables defined in this frame.

global env ──┐
             v
┌───────────────────────────┐
│                           │
│(after call to define)     │
│f:┐                        │<─────────────────────────────┐
└───────────────────────────┘                              │
   │  ^                                                    │
   │  │                                  call to f         │
   v  │                          ┌─────────────────────────┴─┐
  @ @ │                          │x: 5                       │
  │ └─┘                     E1 ->│                           │
  v                              │                           │<───┐
parameter: x                     └───────────────────────────┘    │
((lambda (even? odd?)                                             │
   (set! even? (lambda (n) ...)                                   │
   (set! odd? (lambda (n) ...)             call to letrec/lambda  │
   (even? x))                           ┌─────────────────────────┴─┐
 *unassigned* *unassigned*)             │even?:─────────────────┐   │
                                   E2 ->│odd?:┐                 │   │
                                        │     │                 │   │
                                        └───────────────────────────┘
                                              │  ^              │  ^
                                              │  │              │  │
                                              v  │              v  │
                                             @ @ │             @ @ │
                                             │ └─┘             │ └─┘
                                             v                 v
                                        parameter: n      parameter: n
                                      (if (equal? n 0)  (if (equal? n 0)
                                          false             true
                                          ...               ...

; Let Environment Diagram
; =======================
; even? and odd? procs reference E1 because they are evaluated in the body of
; f but outside the 'let lambda' because they are passed as arguments to that
; lambda.  This means they can't lookup the even? and odd? variables defined
; in E2.

global env ──┐
             v
┌───────────────────────────┐
│                           │
│(after call to define)     │
│f:┐                        │<─────────────────────────────┐
└───────────────────────────┘                              │
   │  ^                                                    │
   │  │                                  call to f         │
   v  │                          ┌─────────────────────────┴─┐
  @ @ │                          │x: 5                       │<───────────┐
  │ └─┘                     E1 ->│                           │<─────────┐ │
  v                              │                           │<───┐     │ │
parameter: x                     └───────────────────────────┘    │     │ │
((lambda (even? odd?)                                             │     │ │
   (even? x))                                                     │     │ │
 (lambda (n) (if (equal? n ...))           call to let/lambda     │     │ │
 (lambda (n) (if (equal? n ...)))       ┌─────────────────────────┴─┐   │ │
                                        │even?:─────────────────┐   │   │ │
                                   E2 ->│odd?:┐                 │   │   ^ │
                                        │     │                 │   │   │ │
                                        └───────────────────────────┘   │ │
                                              │                 │       │ │
                                              │  ┌──────────────────────┘ ^
                                              │  │              │         │
                                              v  │              v         │
                                             @ @ │             @ @        │
                                             │ └─┘             │ └────────┘
                                             v                 v
                                        parameter: n      parameter: n
                                      (if (equal? n 0)  (if (equal? n 0)
                                          false             true
                                          ...               ...
