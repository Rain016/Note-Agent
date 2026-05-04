## Human:
Diffusion Policy 的 forward process 是什麼意思？

## Claude:
Forward process 是 diffusion model 的核心概念之一。
它的意思是把一張乾淨的圖片（或在你的情況下，一個動作序列）
逐步加入 Gaussian noise，經過 T 個步驟之後，
最終變成純粹的 noise。
這個過程是固定的，不需要學習。

## Human:
所以本質上就是一個馬可夫鏈？

## Claude:
對！你理解得很好。
Forward process 確實是一個馬可夫鏈，
每一步只依賴上一步的狀態，
數學上可以寫成 q(x_t | x_{t-1})。