<script lang="ts">
	let size = '60px';
	let unit = 'px';
	let pause = false;
	let ballTopLeft = '#FF3E00';
	let ballTopRight = '#F8B334';
	let ballBottomLeft = '#40B3FF';
	let ballBottomRight = '#676778';
	let duration = '1.5s';
</script>

<div
	class="wrapper"
	style="--size: {size}{unit}; --floatSize: {size}; --ballTopLeftColor: {ballTopLeft}; --ballTopRightColor: {ballTopRight}; --ballBottomLeftColor: {ballBottomLeft}; --ballBottomRightColor: {ballBottomRight}; --duration: {duration};"
>
	<div class="inner">
		<div class="ball-container" class:pause-animation={pause}>
			<div class="single-ball">
				<div class="ball ball-top-left" class:pause-animation={pause}>&nbsp;</div>
			</div>
			<div class="contener_mixte">
				<div class="ball ball-top-right" class:pause-animation={pause}>&nbsp;</div>
			</div>
			<div class="contener_mixte">
				<div class="ball ball-bottom-left" class:pause-animation={pause}>&nbsp;</div>
			</div>
			<div class="contener_mixte">
				<div class="ball ball-bottom-right" class:pause-animation={pause}>&nbsp;</div>
			</div>
		</div>
	</div>
</div>

<style>
	.wrapper {
		width: var(--size);
		height: var(--size);
		display: flex;
		justify-content: center;
		align-items: center;
		line-height: 0;
		box-sizing: border-box;
	}
	.inner {
		transform: scale(calc(var(--floatSize) / 52));
	}
	.ball-container {
		animation: ballTwo var(--duration) infinite;
		width: 44px;
		height: 44px;
		flex-shrink: 0;
		position: relative;
	}
	.single-ball {
		width: 44px;
		height: 44px;
		position: absolute;
	}
	.ball {
		width: 20px;
		height: 20px;
		border-radius: 50%;
		position: absolute;
		animation: ballOne var(--duration) infinite ease;
	}
	.pause-animation {
		animation-play-state: paused;
	}
	.ball-top-left {
		background-color: var(--ballTopLeftColor);
		top: 0;
		left: 0;
	}
	.ball-top-right {
		background-color: var(--ballTopRightColor);
		top: 0;
		left: 24px;
	}
	.ball-bottom-left {
		background-color: var(--ballBottomLeftColor);
		top: 24px;
		left: 0;
	}
	.ball-bottom-right {
		background-color: var(--ballBottomRightColor);
		top: 24px;
		left: 24px;
	}
	@keyframes ballOne {
		0% {
			position: absolute;
		}
		50% {
			top: 12px;
			left: 12px;
			position: absolute;
			opacity: 0.5;
		}
		100% {
			position: absolute;
		}
	}
	@keyframes ballTwo {
		0% {
			transform: rotate(0deg) scale(1);
		}
		50% {
			transform: rotate(360deg) scale(1.3);
		}
		100% {
			transform: rotate(720deg) scale(1);
		}
	}
</style>