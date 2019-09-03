(define (enumerate-interval start end)
  (define (iter cur result)
    (if (> cur end)
        result
        (iter
          (+ cur 1)
          (append
            result
            (list cur)))))
  (iter start '()))

(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op
        (car sequence)
        (accumulate op initial (cdr sequence)))))

(define (flatmap f sequence)
  (accumulate
    append
    '()
    (map
      f
      sequence)))

(define (unique-pairs n)
  (flatmap
    (lambda (i)
      (map
        (lambda (j) (list i j))
        (enumerate-interval 1 (- i 1))))
    (enumerate-interval 1 n)))

(define (prime? num)
  (define (smallest-divisor n)
    (define (find-divisor n test-divisor)
      (cond ((> (square test-divisor) n) n)
            ((= (remainder n test-divisor) 0) test-divisor)
            (else (find-divisor n (+ test-divisor 1)))))
    (find-divisor n 2))
  (= (smallest-divisor num) num))

(define (prime-sum-pairs n)
  (map
    (lambda (p)
      (list
        (car p)
        (cadr p)
        (+ (car p) (cadr p))))
    (filter
      (lambda (p)
        (prime? (+ (car p) (cadr p))))
      (unique-pairs n))))
