(load "6.scm")

(define (make-let bindings body)
  (cons 'let (cons bindings body)))

(define (let*->nested-lets exp env)
  (let ((bindings (let-bindings exp))
        (body (let-body exp)))
    (make-let
      (list (car bindings))
      (if (null? (cdr bindings))
          body
          (list
            (let*->nested-lets
              (cons (cdr bindings)
                    body)))))))

(put 'let* 'eval (lambda (exp env)
                   (eval exp env)))
