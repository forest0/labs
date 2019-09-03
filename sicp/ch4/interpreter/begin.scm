(define (install-syntax-begin eval-table)
  (define eval (eval-table 'get 'eval))

  (define (make-begin actions)
    (cons 'begin actions))
  (define (begin-actions exp)
    (cdr exp))

  (define (eval-begin exp env)
    (let ((actions (begin-actions exp)))
      (if (null? actions)
          (eval 'false env)
          ((eval-table 'get 'sequence) (begin-actions exp) env))))

  (eval-table 'put 'make-begin make-begin)
  (eval-table 'put 'begin eval-begin)
  'done)
