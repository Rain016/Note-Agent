## Human:
Forward process 的數學公式是什麼？

## Claude:
Forward process 的核心公式是：

$$q(x_t | x_{t-1}) = \mathcal{N}(x_t; \sqrt{1-\beta_t} x_{t-1}, \beta_t I)$$

其中 $\beta_t$ 是每個時間步的 noise schedule，$x_t$ 是第 $t$ 步的結果。

## Human:
那一步到位的公式呢？

## Claude:
可以直接從 $x_0$ 跳到任意時間步 $t$：

$$q(x_t | x_0) = \mathcal{N}(x_t; \sqrt{\bar{\alpha}_t} x_0, (1-\bar{\alpha}_t) I)$$

其中 $\bar{\alpha}_t = \prod_{s=1}^{t} (1 - \beta_s)$，這個公式讓訓練更有效率。

## Human:
所以加噪聲的過程可以寫成？

## Claude:
對，可以寫成：

$$x_t = \sqrt{\bar{\alpha}_t} x_0 + \sqrt{1-\bar{\alpha}_t} \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)$$

這樣就可以在訓練時直接從 $x_0$ 採樣到任意 $x_t$，不需要一步一步加噪聲。