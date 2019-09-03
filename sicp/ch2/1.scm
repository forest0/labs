(define (make-rat n d)
  (define g (gcd n d))
  (let ((new-n (/ n g))
        (new-d (/ d g)))
    (if (or
          (and
            (> new-n 0)
            (< new-d 0))
          (and
            (< new-n 0)
            (< new-d 0)))
        (cons (- new-n) (- new-d))
        (cons new-n new-d))))
