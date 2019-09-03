(define (split s1 s2)
  (lambda (painter n)
    (if (= n 0)
        painter
        (let ((smaller
                ((split s1 s2)
                 painter
                 (- n 1))))
          (s1 painter (s2 smaller smaller))))))
