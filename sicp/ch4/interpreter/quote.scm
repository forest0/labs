(define (install-syntax-quote eval-table)
  (define (text-of-quotation exp)
    (cadr exp))

  (define (eval-quote exp env)
    (text-of-quotation exp))

  (eval-table 'put 'quote eval-quote)
  'done)
