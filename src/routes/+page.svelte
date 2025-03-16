<script lang="ts">
    import { onMount } from "svelte";
  	import "../app.css";
  	import { readTextFileLines, readTextFile, exists, mkdir, BaseDirectory } from "@tauri-apps/plugin-fs";
	import {basename, appLocalDataDir, sep} from '@tauri-apps/api/path';
	import { modals, Modals } from 'svelte-modals'
	import SelectFileModal from '../modals/SelectFileModal.svelte'
	import { fade } from 'svelte/transition'
    import { csvFile } from "../store";
	import axios from 'axios'
	import { Command } from '@tauri-apps/plugin-shell';
    import LoadingIndicator from "../components/LoadingIndicator.svelte";

	let isLoading = $state(false)

	//{"symbol" : row[5], 'date': date, "quantity": quantity, 'gengi': gengi, "basis": costBasis, "basisISK": priceISK}
	interface Trade {
		symbol:string;
		date:string;
		quantity:number;
		gengi:number;
		currency:string;
		basis:number;
		basisISK:number;
	}

	interface StockSummary {
		symbol: string;
		kaupverd: number;
		quantity: number;
	}

	let trades:Trade[] = $state([])
	let stockSummary:StockSummary[] = $state([]);
	
	onMount(async () => {
		let localDataDir = await appLocalDataDir()
		console.log(localDataDir)
		if(!await exists(localDataDir)){
			await mkdir(localDataDir)
		}
	})

	csvFile.subscribe(async (value) => {
		if(value){
			readCsvFile(value)
		}
	})

	function openSelectFileModal(){
		modals.open(SelectFileModal)
	}

	async function readCsvFile(filePath:string){
		isLoading = true
		trades = []
		stockSummary = []
		console.log('run parser')
		const command = Command.sidecar('../backend/parser/parser/parser', [filePath]);
		const output = await command.execute();
		console.log(output)
		if(output.code == 0){
			let data = JSON.parse(output.stdout)
			console.log(data)
			for(let i in data.trades){
				trades = [...trades, data.trades[i]]
			}
			for(let i in data.summary){
				stockSummary = [...stockSummary, data.summary[i]]
			}
		}

		isLoading = false
	}

</script>

<main class="flex-col h-screen p-8">
	<div class='flex justify-between'>
		<div class='flex items-center my-2'>
			<button class='bg-sky-600 mr-4' onclick={openSelectFileModal}>Select .csv file</button>
			{#if $csvFile}
				<p class='text-slate-400 my-4'>{$csvFile}</p>
			{/if}
		</div>
		{#if $csvFile}
		<div class='flex items-center'><button class='border border-slate-200 bg-slate-700' onclick={() => readCsvFile($csvFile)}>&#8635;</button></div>
		{/if}
	</div>
	<!--<button onclick={() => {readCsvFile($csvFile)}}>Send request</button>-->
	<div class='flex flex-col items-center'>
		{#if isLoading}
			<div>
				<LoadingIndicator/>
				<p class='text-slate-400 mt-3'>Les gögn...</p>
			</div>
		{:else if trades.length > 0}
			<div class='w-full border border-slate-300 rounded-lg overflow-auto'>
				<table class='w-full'>
					<thead>
						<tr class='text-slate-200'>
							<th>Symbol</th>
							<th>Date</th>
							<th>Quantity</th>
							<th>Currency</th>
							<th>Gengi</th>
							<th>Basis</th>
							<th>Basis ISK</th>
						</tr>
					</thead>
					<tbody>
						{#each trades as line, i}
						<tr class={`text-slate-300 ${i % 2 == 0 ? 'bg-slate-600' : 'bg-slate-700'}`}>
							<td>{line.symbol}</td>
							<td>{line.date}</td>
							<td>{line.quantity}</td>
							<td>{line.currency}</td>
							<td>{line.gengi}</td>
							<td>{line.basis.toLocaleString()}</td>
							<td>{line.basisISK.toLocaleString()}</td>
						</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<div class='flex w-full items-end my-4'>
				<div class='border border-slate-300 rounded-lg overflow-auto'>
					<table>
						<thead>
							<tr class='text-slate-200'>
								<th>Symbol</th>
								<th>Quantity</th>
								<th>Kaupverð</th>
							</tr>
						</thead>
						<tbody>
							{#each stockSummary as line, i}
							<tr class={`text-slate-300 ${i % 2 == 0 ? 'bg-slate-600' : 'bg-slate-700'}`}>
								<td>{line.symbol}</td>
								<td>{line.quantity}</td>
								<td>{line.kaupverd.toLocaleString()}</td>
							</tr>
							{/each}
						</tbody>
					</table>
				</div>
				<div class='flex justify-center text-slate-300 font-bold ml-4'>
					<p class='mr-3'>Kaupverð samtals:</p>
					<p>{stockSummary.reduce((a, b) => a + b.kaupverd, 0).toLocaleString()}</p>
				</div>
			</div>
		{/if}
	</div>
</main>

<Modals>
	<!-- shown when any modal is opened -->
	{#snippet backdrop({ close })}
	  <div
		class="backdrop"
		onclick={() => close()}
		transition:fade|global={{duration: 150}}
	  />
	{/snippet}
</Modals>

<style>
	.backdrop {
	  position: fixed;
	  top: 0;
	  bottom: 0;
	  right: 0;
	  left: 0;
	  background: rgba(0,0,0,0.50)
	}

	td, th{
		text-align: center;
		padding: 0.5rem 1rem;
	}
</style>

