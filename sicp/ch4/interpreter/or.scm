(define (install-syntax-or eval-table)
  (define eval (eval-table 'get 'eval))

  (define (expand-or exp env)
    (if (null? exp)
        (eval 'false env)
        (let ((leftmost (eval (car exp) env)))
          (if (true? leftmost)
              leftmost
              (expand-or (cdr exp) env)))))

  (define (eval-or exp env)
    (expand-or (cdr exp) env))

  (eval-table 'put 'or eval-or)
  'done)
