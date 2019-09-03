(define (find-binding var env recursive?)
  (define (first-variable bindings)
    (caar bindings))
  (define (env-loop cur-env)
    (define (scan bindings)
      (cond ((null? bindings)
             (if recursive?
                 (env-loop (enclosing-environment cur-env))
                 'false))
            ((eq? var (first-variable bindings))
             (car bindings))
            (else (scan (cdr bindings)))))
    (if (null? cur-env)
        'false
        (scan (first-frame cur-env))))
  (env-loop env))

(define (lookup-variable-value var env)
  (let ((binding (find-binding var env #t)))
    (if (pair? binding)
        (let ((val (binding-val binding)))
          (if (eq? val '*unassigned*)
              (error "Unassigned variable -- LOOKUP" var)
              val))
        (error "Unbound variable -- LOOKUP" var))))

(define (scan-out-defines body)
  (let ((define-statements (filter definition? body))
        (body-statements (filter (lambda (s) (not definition?)))))
    (if (null? define-statements)
        body ; no define statement
        (let
          ((variables (map define-variable define-statements))
           (expressions (map definition-value define-statements)))
          (let ((ret (make-let
                       (map (lambda (v) (list v '*unassigned*))
                            variables) ; bindings
                       (append ; body = set! + remain
                         (map (lambda (s) (cons 'set! s))
                              (zip variables expressions)) ; set!
                         body-statements)))) ; remain
            (list ret))))))
