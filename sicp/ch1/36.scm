(define (make-printer start-number)
  (let ((cnt start-number))
    (lambda (msg)
      (display cnt)
      (display " ")
      (display msg)
      (newline)
      (set! cnt (+ cnt 1)))))

(define (fixed-point f first-guess update)
  (define print (make-printer 0))
  (define (close-enough? v1 v2)
    (< (abs (- v1 v2)) 0.00001))
  (define (try guess)
    (print guess)
    (let ((next (update guess (f guess))))
      (if (close-enough? guess next)
          next
          (try next))))
  (try first-guess))

; with average damping
(fixed-point
  (lambda (x) (/ (log 1000) (log x)))
  4.5
  (lambda (before after)
    (/ (+ before after) 2)))

(display "***************")

; without average damping
(fixed-point
  (lambda (x) (/ (log 1000) (log x)))
  4.5
  (lambda (before after)
    after))
