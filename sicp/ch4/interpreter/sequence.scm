(define (install-syntax-sequence eval-table)
  (define eval (eval-table 'get 'eval))
  (define (last-exp? exps) (null? (cdr exps)))
  (define (first-exp exps) (car exps))
  (define (rest-exps exps) (cdr exps))

  (define (eval-sequence exps env)
    (if (last-exp? exps)
        (eval (first-exp exps) env)
        (begin
          (eval (first-exp exps) env)
          (eval-sequence (rest-exps exps) env))))

  (define (sequence->exp seq)
    (cond ((null? seq) seq)
          ((last-exp? seq) (first-exp seq))
          (else
            ((eval-table 'get 'make-begin) seq))))

  (eval-table 'put 'sequence eval-sequence)
  (eval-table 'put 'sequence->exp sequence->exp)
  'done)
