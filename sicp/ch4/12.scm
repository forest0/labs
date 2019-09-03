(define make-frame zip)

; insert to the second item, 1-indexed
(define (add-binding-to-frame! var val frame)
  (set-cdr! frame (cons (list var val)
                        (cdr frame))))

(define (find-binding var env recursive?)
  (define (env-loop cur-env)

    (define (scan bindings)
      (cond ((null? bindings)
             (if recursive?
                 (env-loop (enclosing-environment cur-env))
                 'false))
            ((eq? var (first-variable bindings))
             (car bindings))
            (else (scan (cdr bindings)))))

    (if (eq? cur-env the-empty-environment)
        'false
        (scan (first-frame cur-env))))

  (env-loop env))

(define (update-binding! binding val)
  (set-cdr! binding (list val)))

(define (binding-var binding)
  (car binding))

(define (binding-val binding)
  (cadr binding))

(define (lookup-variable-value var env)
  (let ((binding (find-binding var env #t)))
    (if (pair? binding)
        (binding-val binding)
        (error "Unbound variable -- LOOKUP" var))))

(define (set-variable-value! var val env)
  (let ((binding (find-binding var env #t)))
    (if (pair? binding)
        (update-binding! binding val)
        (error "Unbound variable -- SET!" var))))

(define (define-variable! var val env)
  (let ((binding (find-binding var env #f)))
    (if (pair? binding)
        (update-binding! binding val)
        (add-binding-to-frame! var val (first-frame env)))))
