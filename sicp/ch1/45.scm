(define (make-printer start-number)
  (let ((cnt start-number))
    (lambda (msg)
      (display cnt)
      (display " ")
      (display msg)
      (newline)
      (set! cnt (+ cnt 1)))))

(define (fixed-point f first-guess)
  (define print (make-printer 0))
  (define max-try 10000)

  (define (close-enough? v1 v2)
    (< (abs (- v1 v2)) 0.00001))

  (define (try guess cnt)
    ; debug
    (print guess)
    (let ((next (f guess)))
      (cond ((> cnt max-try); debug
             (display "max-try limit!")
             0)
            ((close-enough? guess next)
             next)
            (else
              (try next (+ cnt 1))))))

  (try first-guess 0))

(define (compose f g)
  (lambda (x)
    (f (g x))))

(define (repeated f n)
  (define (iter i repeat-f)
    (if (= i 1)
        repeat-f
        (iter
          (- i 1)
          (compose f repeat-f))))
  (iter n f))

(define (average-damp f)
   (lambda (x)
     (/
       (+ x
          (f x))
       2)))

(define (average-damp-n-times f n)
  ((repeated average-damp n) f))

(define (pow base exp)
  (define (pow-iter b e result)
    (cond ((= e 0) result)
          ((even? e)
           (pow-iter
             (* b b)
             (/ e 2)
             result))
          (else
            (pow-iter
              b
              (- e 1)
              (* result b)))))
  (pow-iter base exp 1))

(define (nth-root n damp-times)
  (lambda (x)
    (fixed-point
      (average-damp-n-times
        (lambda (y)
          (/ x
             (pow y (- n 1))))
        damp-times)
      1.0)))



; ************************************************
; experiment part
;
; test one-by-one to find the pattern
(define (test-nth-root n damp-times)
  ((nth-root n damp-times) (pow 3 n)))

(define 2th-root (nth-root 2 1))
(define 3th-root (nth-root 3 1))


(define 4th-root (nth-root 4 2))
; ...
(define 7th-root (nth-root 7 2))


(define 8th-root (nth-root 8 3))
; ...
(define 15th-root (nth-root 15 3))


(define 16th-root (nth-root 15 4))
; ...
(define 31th-root (nth-root 31 4))


(define 32th-root (nth-root 32 5))
; ...
(define 63th-root (nth-root 63 5))

; we can find that, n-th root at least need
; \lfloor log_2(n) \rfloor average damp
; ************************************************



(define (floored-log-2 n)
  (define (iter i result)
    (if (< i 2)
        result
        (iter (/ i 2) (+ result 1))))
  (iter n 0))


; finally
(define (nth-root-auto n)
  (lambda (x)
    (fixed-point
      (average-damp-n-times
        (lambda (y)
          (/ x
             (pow y (- n 1))))
        (floored-log-2 n))
      1.0)))
