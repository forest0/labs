(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op
        (car sequence)
        (accumulate op initial (cdr sequence)))))

(define fold-right accumulate)

(define (fold-left op initial sequence)
  (define (iter result rest)
    (if (null? rest)
        result
        (iter
          (op
            result
            (car rest))
          (cdr rest))))
  (iter initial sequence))

(define (reverse-v1 sequence)
  (fold-right
    (lambda (x y)
      (append
        y
        (list x)))
    '()
    sequence))

(define (reverse-v2 sequence)
  (fold-left
    (lambda (x y)
      (append
        (list y)
        x))
    '()
    sequence))
