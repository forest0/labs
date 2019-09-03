(define (empty-set? set)
  (null? set))

(define (element-of-set? x set)
  (cond ((empty-set? set) #f)
        ((equal? x (car set)) #t)
        (else
          (element-of-set? x (cdr set)))))

; allow duplicate
(define (adjoin-set x set)
  (cons x set))

(define (union-set set1 set2)
  (define (iter set result)
    (if (empty-set? set)
        result
        (let ((cur (car set))
              (remain (cdr set)))
          (if (element-of-set? cur result)
              (iter remain result)
              (iter remain (cons cur result))))))
  (iter (append set1 set2) '()))

(define (intersection-set set1 set2)
  (define (iter set result)
    (if (empty-set? set)
        result
        (let ((cur (car set))
              (remain (cdr set)))
          (if (and (element-of-set? cur set2)
                   (not (element-of-set? cur result)))
              (iter remain (cons cur result))
              (iter remain result)))))
  (iter set1 '()))
