(define (install-syntax-let eval-table)
  (define eval (eval-table 'get 'eval))
  (define make-lambda (eval-table 'get 'make-lambda))
  (define make-begin (eval-table 'get 'make-begin))
  (define make-define (eval-table 'get 'make-define))

  (define (named-let? exp)
    (not (pair? (cadr exp))))
  (define (let-bindings exp)
    (if (named-let? exp)
        (caddr exp)
        (cadr exp)))
  (define (let-body exp)
    (if (named-let? exp)
        (cdddr exp)
        (cddr exp)))

  (define (let->lambda exp)
    (let ((bindings (let-bindings exp)))
      ; use cons here instead of list to make sure args are not nested
      ; ((lambda (param1 param2) body) arg1 arg2)
      (cons
        (make-lambda
          (map car bindings)
          (let-body exp))
        (map cadr bindings))))

  (define (let*->nested-lets exp)
    (let ((bindings (let-bindings exp))
          (body (let-body exp)))
      (make-let
        (list (car bindings))
        (if (null? (cdr bindings))
            body
            (list
              (let*->nested-lets
                (cons 'let*
                      (cons (cdr bindings)
                            body))))))))
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

  ; letrec
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

  (define (eval-let exp env)
    (eval (let->derived exp) env))

  (define (let->derived exp)
    (if (named-let? exp)
        (let->combination exp)
        (let->lambda exp)))

  (define (eval-let* exp env)
    (eval (let*->nested-lets exp) env))

  (define (make-let bindings body)
    (cons 'let (cons bindings body)))

  (define (eval-letrec exp env)
    (eval (letrec->let exp) env))

  (eval-table 'put 'let eval-let)
  (eval-table 'put 'let* eval-let*)
  (eval-table 'put 'letrec eval-letrec)
  (eval-table 'put 'make-let make-let)
  'done)

