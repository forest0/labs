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

(define (make-record key value)
  (cons key value))

(define (get-key record)
  (car record))

(define (get-value record)
  (cdr record))

(define (lookup given-key set-of-records)
  (if (empty-tree? set-of-records)
      #f
      (let ((key (get-key (entry set-of-records)))
            (lb (left-branch set-of-records))
            (rb (right-branch set-of-records)))
        (cond ((= key given-key)
               (entry set-of-records))
              ((< key given-key)
               (lookup given-key rb))
              (else
                (lookup given-key lb))))))
