(define (make-monitored f)
  (let ((cnt 0))
    (lambda (input)
      (cond ((eq? input 'how-many-calls?) cnt)
            ((eq? input 'reset-count)
             (set! cnt 0))
            (else
              (set! cnt (+ cnt 1))
              (f input))))))
