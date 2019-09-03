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

(define (queens board-size)

  (define empty-board '())
  (define (make-point x y) (list x y))
  (define (x-point z) (car z))
  (define (y-point z) (cadr z))

  (define (safe? k positions)

    (define (same-row? p1 p2)
      (= (y-point p1) (y-point p2)))
    (define (same-col? p1 p2)
      (= (x-point p1) (x-point p2)))
    (define (same-diagonal? p1 p2)
      (=
        (abs (- (x-point p1) (x-point p2)))
        (abs (- (y-point p1) (y-point p2)))))
    (define (two-position-safe? p1 p2)
      (not
        (or
          (same-row? p1 p2)
          (same-col? p1 p2)
          (same-diagonal? p1 p2))))

    (define (iter p ps)
      (cond ((null? ps) #t)
            ((two-position-safe? p (car ps))
             (iter p (cdr ps)))
            (else #f)))

    (iter (car positions) (cdr positions)))

  (define (adjoin-position new-row k rest-of-queens)
    (cons
      (make-point k new-row)
      rest-of-queens))

  (define (queen-cols k)
    (if (= k 0)
        (list empty-board)
        (filter
          (lambda (positions) (safe? k positions))
          (flatmap
            (lambda (rest-of-queens)
              (map
                (lambda (new-row)
                  (adjoin-position
                    new-row k rest-of-queens))
                (enumerate-interval 1 board-size)))
            (queen-cols (- k 1))))))
  (queen-cols board-size))

(define (queens-solution-amount n)
  (accumulate
    +
    0
    (map
      (lambda (x) 1)
      (queens n))))
