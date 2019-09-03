(define (make-leaf symbol weight)
  (list 'leaf symbol weight))

(define (leaf? object)
  (eq? (car object) 'leaf))

(define (symbol-leaf x) (cadr x))

(define (weight-leaf x) (caddr x))

(define (make-code-tree left right)
  (list left
        right
        (append (symbols left) (symbols right))
        (+ (weight left) (weight right))))

(define (left-branch tree) (car tree))

(define (right-branch tree) (cadr tree))

(define (symbols tree)
  (if (leaf? tree)
      (list (symbol-leaf tree))
      (caddr tree)))

(define (weight tree)
  (if (leaf? tree)
      (weight-leaf tree)
      (cadddr tree)))

(define (decode bits tree)
  (define (choose-branch bit branch)
    (cond ((= bit 0) (left-branch branch))
          ((= bit 1) (right-branch branch))
          (else (error "bad bit: CHOOSE-BRANCH" bit))))
  (define (decode-1 bits current-branch)
    (if (null? bits)
        '()
        (let ((next-branch
                (choose-branch (car bits) current-branch)))
          (if (leaf? next-branch)
              (cons (symbol-leaf next-branch)
                    (decode-1 (cdr bits) tree))
              (decode-1 (cdr bits) next-branch)))))

  (decode-1 bits tree))

(define (adjoin-set x set)
  (if (null? set)
      (list x)
      (if (< (weight x) (weight (car set)))
          (cons x set)
          (cons (car set) (adjoin-set x (cdr set))))))

(define (make-leaf-set pairs)
  (if (null? pairs)
      '()
      (adjoin-set (make-leaf (caar pairs)
                             (cadar pairs))
                  (make-leaf-set (cdr pairs)))))

(define sample-tree
  (make-code-tree (make-leaf 'A 4)
                  (make-code-tree
                    (make-leaf 'B 2)
                    (make-code-tree
                      (make-leaf 'D 1)
                      (make-leaf 'C 1)))))

(define sample-message '(0 1 1 0 0 1 0 1 0 1 1 1 0))

; (decode sample-message sample-tree)
; (a d a b b c a)

(define (symbol-in-tree? symbol tree)
  (not (false?
         (find (lambda (x) (eq? x symbol))
               (symbols tree)))))

(define (encode message tree)
  (define (encode-symbol symbol tree)
    (if (leaf? tree)
        '()
        (let ((lb (left-branch tree))
              (rb (right-branch tree)))
          (cond ((symbol-in-tree? symbol lb)
                 (cons 0
                       (encode-symbol symbol lb)))
                ((symbol-in-tree? symbol rb)
                 (cons 1
                       (encode-symbol symbol rb)))
                (else
                  (error "symbol not in tree -- " symbol))))))
  (if (null? message)
      '()
      (append (encode-symbol (car message) tree)
              (encode (cdr message) tree))))

(define (generate-huffman-tree pairs)
  (define (successive-merge pairs)
    (define (merge-iter pairs n)
      (if (= 1 n)
          (car pairs)
          (let ((one (car pairs))
                (two (cadr pairs))
                (remain-pairs (cddr pairs)))
            (let ((new-node (make-code-tree one two)))
              (merge-iter
                (adjoin-set new-node remain-pairs)
                (- n 1))))))
    (merge-iter pairs (length pairs)))
  (successive-merge (make-leaf-set pairs)))
