(define (install-syntax-lambda eval-table)
  (define make-procedure (eval-table 'get 'make-procedure))
  (define (make-lambda parameters body)
    (cons 'lambda (cons parameters body)))

  (define (lambda-parameters exp) (cadr exp))
  (define (lambda-body exp) (cddr exp))

  (define (eval-lambda exp env)
    (make-procedure (lambda-parameters exp)
                    (lambda-body exp)
                    env))

  (eval-table 'put 'make-lambda make-lambda)
  (eval-table 'put 'lambda eval-lambda)
  'done)
