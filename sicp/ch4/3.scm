(define (install-interpretor-package)

  (define (self-evaluating? exp)
    (cond ((number? exp) true)
          ((string? exp) true)
          (else false)))

  (define (variable? exp) (symbol? exp))
  (define (application? exp) (pair? exp))
  (define (no-operands? exp) (null? exp))

  (define (operator exp) (car exp))
  (define (operands exp) (cdr exp))
  (define (first-operand ops) (car ops))
  (define (rest-operands ops) (cdr ops))

  (define (list-of-values exps env)
    (if (no-operands? exps)
        '()
        (let ((left (eval (first-operand exps) env)))
          (cons left
                (list-of-values (rest-operands exps) env)))))

  (define eval-table (make-table))
  (define (get type operation)
    ((eval-table 'lookup) (list type operation)))
  (define (put type operation f)
    ((eval-table 'insert!) (list type operation) f))

  (define (eval-new env)
    (cond ((self-evaluating? exp) exp)
          ((variable? exp) exp)
          (else
            (let ((eval-proc (get (operator exp) 'eval)))
              ; (display eval-proc)
              (cond (eval-proc
                      (eval-proc (operands exp) env))
                    ((application? exp)
                     ; (let ((opr (eval (operator exp) env))
                     ;       (ops (operands exp)))
                     ;   (if (eq? opr 'lambda)
                     ;       (apply opr (cons (first-operand ops)
                     ;                        (list-of-values (rest-operands ops) env)))
                     ;       (apply (eval (operator exp) env)
                     ;              (list-of-values (operands exp) env)))))
                     (apply-new (eval (operator exp) env)
                                (list-of-values (operands exp) env)))
                    (else (error "Unknown expression type -- EVAL" (list exp env))))))))

  (define (true? exp) (not (eq? exp 'false))) ; how to represent boolean?
  (define (eval-if exp env)
    (define (if-predicate exp) (car exp))
    (define (if-consequent exp) (cadr exp))
    (define (if-alternative exp)
      (if (null? (cddr exp))
          'false
          (caddr exp)))
    (if (true? (eval (if-predicate exp) env))
        (eval (if-consequent exp) env)
        (eval (if-alternative exp) env)))

  (load "../ch3/25.scm") ; table

  (put 'if 'eval eval-if))
