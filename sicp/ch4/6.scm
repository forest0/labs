(load "5.scm")

(define (let-bindings exp) (car exp))
(define (let-body exp) (cdr exp))

(define (let->lambda exp)
  (let ((bindings (let-bindings exp)))
    (cons
      (make-lambda
        (map car bindings)
        (let-body exp))
      (map cadr bindings))))

(put 'let 'eval (lambda (exp env)
                  (eval exp env)))
