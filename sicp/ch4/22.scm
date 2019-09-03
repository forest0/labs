(define (let->lambda exp)
  (let ((bindings (let-bindings exp)))
    ; use cons here instead of list to make sure args are not nested
    ; ((lambda (param1 param2) body) arg1 arg2)
    (cons
      (make-lambda
        (map car bindings)
        (let-body exp))
      (map cadr bindings))))

; named let
; syntax: (let ⟨var⟩ ⟨bindings⟩ ⟨body⟩)
(define (let->combination exp)
  (define (parameters exp)
    (map car (let-bindings exp)))
  (define (initial-arguments exp)
    (map cadr (let-bindings exp)))
  (let ((proc-name (cadr exp)))
    (make-begin
      (list
        ; define it first
        (make-define
          (cons proc-name (parameters exp))
          (let-body exp))
        ; call it
        (cons proc-name (initial-arguments exp))))))

(define (let->derived exp)
  (if (named-let? exp)
      (let->combination exp)
      (let->lambda exp)))

(define (analyze exp)
  (cond ((self-evaluating? exp)
         (analyze-self-evaluating exp))
        ((quoted? exp) (analyze-quoted exp))
        ((variable? exp) (analyze-variable exp))
        ((assignment? exp) (analyze-assignment exp))
        ((definition? exp) (analyze-definition exp))
        ((if? exp) (analyze-if exp))
        ((lambda? exp) (analyze-lambda exp))
        ((begin? exp) (analyze-sequence (begin-actions exp)))
        ((cond? exp) (analyze (cond->if exp)))
        ((let? exp) (analyze (let->derived exp))) ; add let here
        ((application? exp) (analyze-application exp))
        (else (error "Unknown expression type: ANALYZE" exp))))

