(define (install-syntax-and eval-table)
  (define eval (eval-table 'get 'eval))

  (define (expand-and exp env)
    (let ((leftmost (eval (car exp) env)))
      (if (true? leftmost)
          (if (null? (cdr exp))
              leftmost
              (expand-and (cdr exp) env))
          (eval 'false env))))

  (define (eval-and exp env)
    (if (null? (cdr exp))
        (eval 'true env)
        (expand-and (cdr exp) env)))

  (eval-table 'put 'and eval-and)
  'done)
