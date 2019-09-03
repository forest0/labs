(define (make-tree entry left right)
  (list entry left right))

(define (entry tree)
  (car tree))

(define (left-branch tree)
  (cadr tree))

(define (right-branch tree)
  (caddr tree))

(define (empty-tree? tree)
  (null? tree))

(define (has-entry? x tree)
  (cond ((empty-tree? #f))
        ((= x (entry tree)) #t)
        ((< x (entry tree))
         (has-entry? x (left-branch tree)))
        (else
          (has-entry? x (right-brach tree)))))

(define (element-of-set? x set)
  (has-entry? x set))

(define (empty-set? set)
  (empty-tree? set))

(define (adjoin-set x set)
  (cond ((empty-set? set) (make-tree x '() '()))
        ((< x (entry set))
         (make-tree (entry set)
                    (adjoin-set x (left-branch set))
                    (right-branch set)))
        (else
          (make-tree (entry set)
                     (left-branch set)
                     (adjoin-set x (right-branch set))))))

(define (list->tree elements)
  (define (partial-tree elts n)
    (if (= n 0)
        (cons '() elts)
        (let ((left-size (quotient (- n 1) 2)))
          (let ((left-result
                  (partial-tree elts left-size)))
            (let ((left-tree (car left-result))
                  (non-left-elts (cdr left-result))
                  (right-size (- n (+ left-size 1))))
              (let ((this-entry (car non-left-elts))
                    (right-result
                      (partial-tree
                        (cdr non-left-elts)
                        right-size)))
                (let ((right-tree (car right-result))
                      (remaining-elts
                        (cdr right-result)))
                  (cons (make-tree this-entry
                                   left-tree
                                   right-tree)
                        remaining-elts))))))))
  (car (partial-tree elements (length elements))))

(define (tree->list tree)
  (define (copy-to-list tree result)
    (if (empty-tree? tree)
        result
        (copy-to-list (left-branch tree)
                      (cons (entry tree)
                            (copy-to-list
                              (right-branch tree)
                              result)))))
  (copy-to-list tree '()))

; list representation
(define (union-set set1 set2)
  (define (empty-set? set)
    (null? set))
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

; awkward
(define (union-tree tree1 tree2)
  (list->tree
    (union-set
      (tree->list tree1)
      (tree->list tree2))))

; list representation
(define (intersection-set set1 set2)
  (define (empty-set? set)
    (null? set))
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

; awkward
(define (intersection-tree tree1 tree2)
  (list->tree
    (intersection-set
      (tree->list tree1)
      (tree->list tree2))))
