(define (find-env var env)
  (define (contains-var? bindings var)
    (cond ((null? bindings) 'false)
          ((eq? (first-variable bindings) var) 'true)
          (else (contains-var? (cdr bindings) var))))
  (cond ((eq? the-empty-environment env) 'false)
        ((contains-var? (frist-frame env)) env)
        (else (find-env var (enclosing-environment env)))))

(define (set-frame! env frame)
  (set-car! env frame))

(define (eval-make-unbound! var env)
  (let ((nearest-env-with-bounding (find-env var env)))
    (if nearest-env-with-bounding
        (set-frame!
          nearest-env-with-bounding
          (filter (lambda (binding)
                    (not (eq? var (binding-var binding))))
                  (first-frame nearest-env-with-bounding))))))
