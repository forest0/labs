(define (install-syntax-if eval-table)
  (define eval (eval-table 'get 'eval))

  (define (make-if predicate consequent alternative)
    (list 'if predicate consequent alternative))

  (define (if-predicate exp) (cadr exp))
  (define (if-consequent exp) (caddr exp))
  (define (if-alternative exp)
    (if (null? (cdddr exp))
        'false
        (cadddr exp)))

  (define (eval-if exp env)
    (if (true? (eval (if-predicate exp) env))
        (eval (if-consequent exp) env)
        (eval (if-alternative exp) env)))

  (eval-table 'put 'if eval-if)
  (eval-table 'put 'make-if make-if)
  'done)
