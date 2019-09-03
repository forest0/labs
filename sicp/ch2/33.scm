(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op
        (car sequence)
        (accumulate op initial (cdr sequence)))))

(define (filter predicate sequence)
  (cond ((null? sequence) '())
        ((predicate (car sequence))
         (cons
           (car sequence)
           (filter predicate (cdr sequence))))
        (else
          (filter predicate (cdr sequence)))))

; (define (map f sequence)
;   (if (null? sequence)
;       '()
;       (cons
;         (f (car sequence))
;         (map f (cdr sequence)))))

(define (map p sequence)
  (accumulate
    (lambda (x y)
      (cons
        (p x)
        y))
    '()
    sequence))

; (define (append seq1 seq2)
;   (if (null? seq1)
;       seq2
;       (cons
;         (car seq1)
;         (append
;           (cdr seq1)
;           seq2))))

(define (append seq1 seq2)
  (accumulate
    cons
    seq2
    seq1))

(define (length sequence)
  (accumulate
    (lambda (x y)
      (+ 1 y))
    0
    sequence))
