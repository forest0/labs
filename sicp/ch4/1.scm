; always left to right
(define (list-of-values exps env)
  (if (no-operands? exps)
      '()
      (let ((left (eval (first-operand exps) env)))
        (let ((rest (list-of-values
                      (rest-operands exps)
                      env)))
          (cons left rest)))))
