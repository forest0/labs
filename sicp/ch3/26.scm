(define (make-tree key value left right)
  (list key value left right))

(define (tree-key tree)
  (car tree))

(define (tree-value tree)
  (cadr tree))

(define (tree-left-branch tree)
  (caddr tree))

(define (tree-right-branch tree)
  (cadddr tree))

(define (tree-empty? tree)
  (null? tree))

(define (tree-set-key! tree new-key)
  (set-car! tree new-key))

(define (tree-set-value! tree new-value)
  (set-car! (cdr tree) new-value))

(define (tree-set-left-branch! tree new-left-branch)
  (set-car! (cddr tree) new-left-branch))

(define (tree-set-right-branch! tree new-right-branch)
  (set-car! (cdddr tree) new-right-branch))

(define (tree-search tree given-key compare)
  (if (tree-empty? tree)
      '()
      (let ((compare-result (compare given-key (tree-key tree))))
        (cond ((= 0 compare-result)
               tree)
              ((< compare-result 0)
               (tree-search (tree-left-branch tree) given-key compare))
              (else
                (tree-search (tree-right-branch tree) given-key compare))))))

(define (tree-insert! tree given-key value compare)
  (if (tree-empty? tree)
      (make-tree given-key value '() '())
      (let ((compare-result (compare given-key (tree-key tree))))
        (cond ((= 0 compare-result)
               (tree-set-value! tree value)
               tree)
              ((< compare-result 0)
               (tree-set-left-branch! tree
                                      (tree-insert!
                                        (tree-left-branch tree)
                                        given-key
                                        value
                                        compare))
               tree)
              (else
                (tree-set-right-branch! tree
                                        (tree-insert!
                                          (tree-right-branch tree)
                                          given-key
                                          value
                                          compare))
                tree)))))

(define (compare-string x y)
  (cond ((string=? x y)
         0)
        ((string<? x y)
         -1)
        (else 1)))

(define (compare-symbol x y)
  (compare-string (symbol->string x)
                  (symbol->string y)))

(define (compare-number x y)
  (- x y))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (make-table compare)
  (let ((local-table '()))
    (define (empty?)
      (null? local-table))
    (define (insert! given-key value)
      (set! local-table (tree-insert! local-table given-key value compare))
      'ok)
    (define (lookup given-key)
      (let ((result (tree-search local-table given-key compare)))
        (if (null? result)
            #f
            (tree-value result))))
    (define (dispatch m)
      (cond ((eq? m 'insert!) insert!)
            ((eq? m 'lookup) lookup)
            ((eq? m 'empty?) empty?)
            (else (error "Unknown operation of table -- DISPATCH" m))))
    dispatch))
