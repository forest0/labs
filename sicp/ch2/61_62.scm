(define (empty-set? set)
  (null? set))

(define (element-of-set? x set)
  (if (empty-set? set)
      #f
      (let ((cur (car set))
            (remain (cdr set)))
        (cond ((= cur x) #t)
              ((< x cur) #f)
              (else
                (element-of-set? x remain))))))

; iterative
(define (adjoin-set x set)
  (define (iter s reversed-list inserted?)
    (cond ((empty-set? s)
           (reverse (cons x reversed-list)))
          (inserted?
           (append (reverse reversed-list) s))
          (else
            (let ((cur (car s))
                  (remain (cdr s)))
              (if (> x cur)
                  (iter remain (cons cur reversed-list) #f)
                  (iter s (cons x reversed-list) #t))))))
  (if (element-of-set? x set)
      set
      (iter set '() #f)))

; recursive
(define (adjoin-set-recursive x set)
  (if (empty-set? set)
      (list x)
      (let ((cur (car set))
            (remain (cdr set)))
        (cond ((= x cur) set)
              ((> x cur)
               (cons cur (adjoin-set-recursive x remain)))
              (else
                (cons x set))))))

(define (union-set set1 set2)
  (define (iter s1 s2 result)
    (cond ((empty-set? s1)
           (append (reverse result) s2))
          ((empty-set? s2)
           (append (reverse result) s1))
          (else
            (let ((cur1 (car s1))
                  (remain1 (cdr s1))
                  (cur2 (car s2))
                  (remain2 (cdr s2)))
              (cond ((= cur1 cur2)
                     (iter remain1 remain2 (cons cur1 result)))
                    ((< cur1 cur2)
                     (iter remain1 s2 (cons cur1 result)))
                    (else
                      (iter s1 remain2 (cons cur2 result))))))))
  (iter set1 set2 '()))

(define (intersection-set set1 set2)
  (define (iter s1 s2 result)
    (if (or (empty-set? s1) (empty-set? s2))
        (reverse result)
        (let ((cur1 (car s1))
              (remain1 (cdr s1))
              (cur2 (car s2))
              (remain2 (cdr s2)))
          (cond ((= cur1 cur2)
                 (iter remain1 remain2 (cons cur1 result)))
                ((< cur1 cur2)
                 (iter remain1 s2 result))
                (else
                  (iter s1 remain2 result))))))
  (iter set1 set2 '()))
