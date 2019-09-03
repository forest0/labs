(define (make-interpreter eval-table)
  ; (define eval-in-underlying-scheme eval)
  (define apply-in-underlying-scheme apply)

  (define (my-apply procedure arguments)
    (cond ((primitive-procedure? procedure)
           (apply-primitive-procedure procedure arguments))
          ((compound-procedure? procedure)
           ((eval-table 'get 'sequence)
            (procedure-body procedure)
            (extend-environment
              (procedure-parameters procedure)
              arguments
              (procedure-environment procedure))))
          (else (error "Unknown procedure type to APPLY --" procedure))))
  (define (my-eval exp env)
    (cond ((self-evaluating? exp) exp)
          ((variable? exp) (lookup-variable-value exp env))
          (else (let ((eval-proc (eval-table 'get (operator exp))))
                  (cond (eval-proc
                          (eval-proc exp env))
                        ((application? exp)
                         (my-apply (my-eval (operator exp) env)
                                (list-of-values (operands exp) env))))))))
  (define (list-of-values exps env)
    (if (no-operands? exps)
        '()
        ; evaluation order is determined by underlying Scheme
        ; (cons (eval (first-operand exps) env)
        ;       (list-of-values (rest-operands exps) env))))
        ;
        ; make sure left to right
        (let ((left (my-eval (first-operand exps) env)))
          (let ((rest (list-of-values
                        (rest-operands exps)
                        env)))
            (cons left rest)))))
  (define (self-evaluating? exp)
    (cond ((number? exp) true)
          ((string? exp) true)
          ((boolean? exp) true)
          (else false)))
  (define (variable? exp) (symbol? exp))
  (define (application? exp) (pair? exp))

  (define (operator exp) (car exp))
  (define (operands exp) (cdr exp))
  (define (no-operands? exp) (null? exp))
  (define (first-operand ops) (car ops))
  (define (rest-operands ops) (cdr ops))

  (define (tagged-list? proc tag)
    (and (pair? proc)
         (eq? (car proc) tag)))

  (define primitive-procedures
    (list (list 'car car)
          (list 'cdr cdr)
          (list 'cons cons)
          (list 'list list)
          (list 'null? null?)
          (list 'not not)
          (list '= =)
          (list '< <)
          (list '> >)
          (list '+ +)
          (list '- -)
          (list '* *)
          (list 'symbol? symbol?)
          (list 'display display)
          (list 'newline newline)))
  (define (primitive-procedure? procedure)
    (tagged-list? procedure 'primitive))
  (define primitive-procedure-names
    (map car primitive-procedures))
  (define primitive-procedure-objects
    (map
      (lambda (proc) (list 'primitive (cadr proc)))
      primitive-procedures))
  (define (primitive-procedure-implementation procedure)
    (cadr procedure))
  (define (apply-primitive-procedure procedure arguments)
    (apply-in-underlying-scheme (primitive-procedure-implementation procedure)
                                arguments))

  (define (make-procedure parameters body env)
    (list 'procedure parameters (scan-out-defines body) env))

  (define (scan-out-defines body)
    (define definition? (eval-table 'get 'definition?))
    (define definition-variable (eval-table 'get 'definition-variable))
    (define definition-value (eval-table 'get 'definition-value))
    (define make-begin (eval-table 'get 'make-begin))
    (define make-let (eval-table 'get 'make-let))
    (define (declare-variables variables)
      (map (lambda (v) (list v '*unassigned*)) variables))
    (define (set-variables bindings)
      (map (lambda (binding) (cons 'set! binding)) bindings))

    (let ((define-statements (filter definition? body))
          (body-statements (filter (lambda (s) (not (definition? s))) body)))
      (if (null? define-statements)
          body ; no define statement
          (let
            ((variables (map definition-variable define-statements))
             (expressions (map definition-value define-statements)))
            (list (make-let
                    (declare-variables variables)
                    (append
                      (set-variables (zip variables expressions))
                      body-statements)))))))

  (define (compound-procedure? p)
    (tagged-list? p 'procedure))
  (define (procedure-parameters p)
    (cadr p))
  (define (procedure-body p)
    (caddr p))
  (define (procedure-environment p)
    (cadddr p))


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
          ; first frame can be empty
          ; e.g. internal define new variable,
          ; while outer define without parameter
          ; see testcases for nested-define
          (if (null? (first-frame env))
              (set-first-frame! env (make-frame (list var) (list val)))
              (add-binding-to-frame! var val (first-frame env))))))


  (define (enclosing-environment env) (cdr env))
  (define (first-frame env) (car env))
  (define set-first-frame! set-car!)

  (define make-frame zip)
  (define make-binding list)
  (define (binding-var binding) (car binding))
  (define (binding-val binding) (cadr binding))
  (define (update-binding! binding val)
    (set-cdr! binding (list val)))
  (define (add-binding-to-frame! var val frame)
    (if (null? (cdr frame))
        (set-cdr! frame (list (list var val)))
        (set-cdr! frame (cons (list var val)
                              (cdr frame)))))
  (define (extend-environment vars vals base-env)
    (if (= (length vars) (length vals))
        (cons (make-frame vars vals) base-env)
        (if (< (length vars) (length vals))
            (error "Too many arguments supplied" vars vals)
            (error "Too few arguments supplied" vars vals))))

  (define the-empty-environment '())
  (define (setup-environment)
    (let ((initial-env
            (extend-environment
              primitive-procedure-names
              primitive-procedure-objects
              the-empty-environment)))
      (define-variable! 'true true initial-env)
      (define-variable! 'false false initial-env)
      (define-variable! '*unassigned* '*unassigned* initial-env)
      (define-variable! 'begin 'begin initial-env)
      initial-env))

  (define the-global-environment (setup-environment))


  (define (dispatch m)
    (cond ((eq? m 'eval) my-eval)
          (else (error "Unknown operation of interpreter basic -- " m))))

  (eval-table 'put 'define-variable! define-variable!)
  (eval-table 'put 'set-variable-value! set-variable-value!)
  (eval-table 'put 'make-procedure make-procedure)
  (eval-table 'put 'the-global-environment the-global-environment)
  (eval-table 'put 'procedure-parameters procedure-parameters)
  (eval-table 'put 'procedure-body procedure-body)
  (eval-table 'put 'eval my-eval)
  (eval-table 'put 'apply my-apply)

  dispatch)
