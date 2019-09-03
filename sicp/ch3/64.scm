(define (sqrt-stream x)
  (define guesses
    (cons-stream 1.0
                 (stream-map (lambda (guess)
                               (/ (+ guess
                                     (/ x guess))
                                  2))
                             guesses)))
  guesses)

(define (stream-limit stream tolerance)
  (let ((cur (stream-car stream))
        (next (stream-car (stream-cdr stream))))
    (if (< (abs (- cur next)) tolerance)
        next
        (stream-limit (stream-cdr stream) tolerance))))

(define (my-sqrt x tolerance)
  (stream-limit (sqrt-stream x) tolerance))
