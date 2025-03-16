<script lang='ts'>
    import { fade } from 'svelte/transition'
    import {csvFile} from '../store'
    import {sep, join, extname, homeDir} from '@tauri-apps/api/path';
    import folder_icon_url from '../../static/folder-icon.svg'
    import file_icon_url from '../../static/file-icon.svg'
    import { readDir, lstat, exists, mkdir, BaseDirectory, create, readTextFile, writeTextFile } from '@tauri-apps/plugin-fs';
	import { onMount } from 'svelte';

    const { type, isOpen, close } = $props()  // type = source, working eða filter

    interface dialogListItem {
        name: string,
        isDir: boolean,
        mtime: Date
    }

    let dialogCurrentPath = $state('')
    let searchBar:HTMLInputElement
    let driveInput:HTMLInputElement
    let selectedFile = $state('')
    let currentFolderContents:dialogListItem[] = $state([]) //listi af öllum möppum og skrám í currentFolder, notað þegar search filterar út úr dialogList en svo ef strokað er út úr searchbar þá er hægt að sækja aftur úr þessum lista
    let dialogList:dialogListItem[] = $state([])
    let recentFiles:string[] = $state([])
    let pathBreakdown:string[] = $state([])
    let dialogListOrder = {orderBy: 'name', descending: true}
    let newFolderName = $state('')
    let message = $state('')
    let driveMessage = $state('')
    let selectDrive = $state(false);

    async function getParentDir(filePath:string){
        return await join(...filePath.split(sep()).slice(0, -1))
    }

    onMount(async () => {
        recentFiles = await getRecentFiles()
        if(recentFiles.length > 0){
            let folder = await getParentDir(recentFiles[0])
            populateDirList(folder)
        }
        else{
            populateDirList(await homeDir())
        }
    })

    async function setFile(){
        if(selectedFile == '') return;

        recentFiles = recentFiles.filter(file => file != selectedFile) //ef currentFolder er í recentFolders, taka hana út þá og setja aftast, ef hún er ekki í þá gerir þessi lína ekkert
        recentFiles.push(selectedFile)
        while(recentFiles.length > 15){
            recentFiles.shift() //taka út fyrsta (elsta) stak
        }
        
        await writeToRecentFilesFile(recentFiles)

        $csvFile = selectedFile

        close()
    }

    async function getRecentFiles(){
        let recentFilesFile = await join('recentFiles', `recentFiles.txt`)
        if(!await exists(recentFilesFile, {baseDir: BaseDirectory.AppLocalData})){
            return []
        }
        let recentFoldersFileContent = await readTextFile(recentFilesFile, {baseDir: BaseDirectory.AppLocalData})
        let recentFoldersList:string[] = []
        if(recentFoldersFileContent.length > 0){
            recentFoldersList = recentFoldersFileContent.split('\n')
        }

        return recentFoldersList
    }

    async function writeToRecentFilesFile(dirList:string[]){
        if(!await exists('recentFiles', {baseDir: BaseDirectory.AppLocalData})){
            await mkdir('recentFiles', {baseDir: BaseDirectory.AppLocalData})
        }

        let recentFoldersFile = await join('recentFiles', `recentFiles.txt`)
        if(!await exists(recentFoldersFile, {baseDir: BaseDirectory.AppLocalData})){
            await create(recentFoldersFile, {baseDir: BaseDirectory.AppLocalData})
        }

        await writeTextFile(recentFoldersFile, dirList.join('\n'), {baseDir: BaseDirectory.AppLocalData})
    }

    function formatTime(date:Date){
        let minutes = date.getMinutes().toString().length == 2 ? date.getMinutes() : `0${date.getMinutes()}`
        return `${date.getDate()}/${date.getMonth()+1}/${date.getFullYear()} ${date.getHours()}:${minutes}`
    }

    async function populateDirList(dir:string){
        if(!dir) return;
        if(dir.endsWith(':')){ //ef ýtt er á C: í pathinu efst í dialoginu þá opnast project base mappan frekar en C: þannig þarf að bæta við \
            dir += '\\'
        }
        message = ''
        searchBar.value = ''
        dialogCurrentPath = dir;
        dialogList = [];
        pathBreakdown = []
        let pathSep = dir.split(sep())
        pathSep[pathSep.length-1] == '' ? pathSep.pop() : null; // ef current path er C:, þá verður pathSep = ['C:', ''], því current path er í rauninni C:\ og pathinu er splittað á \
        pathBreakdown = [...pathSep]
        
        let dirents:any = [];
       
        //Hér er náð í folders og files
        const dirContents = await readDir(dir);
        for (const dirent of dirContents) {
            let isValidFile;
            try {
                isValidFile = await extname(dirent.name) == 'csv'
            } catch {
                isValidFile = false //ef extname kastar error þá er það ekki file
            }
            if(dirent.name[0] != '.' && (dirent.isDirectory || isValidFile)){
                let mtime
                try{
                    let stats = await lstat(await join(dir, dirent.name))
                    mtime = stats.mtime
                } catch(err) {
                    console.log(err)
                    mtime = new Date(0) //sumar directories má ekki lesa stats af, kemur permission error, set bara date sem 1. jan 1970
                }
                dirents.push({name: dirent.name, isDir: dirent.isDirectory, mtime: mtime})
            }
        }
        if(dialogListOrder.orderBy == 'name'){
            if(dialogListOrder.descending){
                dirents.sort((a:dialogListItem, b:dialogListItem) => (a.name.toLowerCase() > b.name.toLowerCase()) ? 1 : ((b.name.toLowerCase() > a.name.toLowerCase()) ? -1 : 0))
            }
            else{
                dirents.sort((a:dialogListItem, b:dialogListItem) => (a.name.toLowerCase() > b.name.toLowerCase()) ? -1 : ((b.name.toLowerCase() > a.name.toLowerCase()) ? 1 : 0))
            }
        }
        else{
            if(dialogListOrder.descending){
                dirents.sort((a:dialogListItem, b:dialogListItem) => (a.mtime.getTime() > b.mtime.getTime()) ? 1 : (b.mtime.getTime() > a.mtime.getTime()) ? -1 : 0)
            }
            else{
                dirents.sort((a:dialogListItem, b:dialogListItem) => (a.mtime.getTime() > b.mtime.getTime()) ? -1 : (b.mtime.getTime() > a.mtime.getTime()) ? 1 : 0)
            }
        }
        
        dialogList = [...dirents]
        currentFolderContents = [...dialogList]
    }

    function goToParentDir(){
        let pathSep = dialogCurrentPath.split(sep())
        if(pathSep.length == 2 && pathSep[pathSep.length-1] == ''){ //ef pathSep = ['C:', ''] þá er currentfolder C:\ og  þarf þá að sýna drives þegar ýtt er á upp takkann
            pathBreakdown = []   
            selectDrive = true;
        }
        else{
            pathSep.pop()
            populateDirList(pathSep.join(sep()))
        }
    }

    async function goToDrive(){
        let drive = driveInput.value.toUpperCase()
        if(drive.length > 0){
            try{
                await populateDirList(`${drive}:\\`)
                driveMessage = ''
                selectDrive = false;
            }
            catch(err){
                console.log(err)
                driveMessage = 'Drive not found'
                selectDrive = true;
                pathBreakdown = []
            }
        }
    }

    async function createNewFolder(newDir:string){
        if(newDir == '') return;
        try{
            let newFolderPath = await join(dialogCurrentPath, newDir)
            if(await exists(newFolderPath)){
                message = 'Folder already exists'
                return;
            }
            else {
                await mkdir(newFolderPath)
                dialogList = [...dialogList, {name: newDir, isDir: true, mtime: new Date()}]
                currentFolderContents = [... dialogList]
                message = ''
                newFolderName = ''
            }
        }
        catch(err){
            message = 'Error creating folder'
        }
    }

    async function searchBarInput(){
        let searchValue = searchBar.value.toLowerCase()
        let searchResults = currentFolderContents.filter(item => item.name.toLowerCase().includes(searchValue))
        dialogList = [...searchResults]
    }

    function getFileName(file:string){
        let split = file.split(sep())
        if(split.length == 2 && split[1] == ''){ //í þessu tilfelli er folder bara drifið þ.e. 'C:\' eða 'D:\' etc.
            return split[0]
        }
        else{
            return split.pop()
        }
    }

    async function removeRecentFolder(folder:string){
        let newRecentFolders = recentFiles.filter(f => f != folder)
        recentFiles = [...newRecentFolders]
        await writeToRecentFilesFile(recentFiles)
    }

</script>

{#if isOpen}
<div role="dialog" id='modal' class='text-slate-600' transition:fade|global={{duration: 150}}>
    <div id='contents' class='h-3/4 w-4/5 flex flex-col justify-between bg-slate-700 text-slate-200 rounded-xl py-2 px-4 border border-slate-500'>
        <!--Header-->
        <div class='border-b border-slate-500 py-2'>
            <h4>Select csv file</h4>
        </div>

        <!--Body-->
        <div class='flex overflow-auto flex-auto text-sm'>

            <!--Recent files-->
            <div class='flex flex-col border-r border-slate-500 w-1/5 text-xs'>
                <div class='border-b h-10 border-slate-500 flex items-center'>
                    <h5 class='p-1'>Recent files</h5>
                </div>
                <div class='flex-auto overflow-auto'>
                    <div class='flex flex-col overflow-auto'>
                        {#each [...recentFiles].reverse() as file}
                            <div class='hover:bg-slate-600 cursor-pointer flex justify-between'>
                                <!-- svelte-ignore a11y_click_events_have_key_events -->
                                <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                                 <div class='grow h-8 flex items-center pl-1' onclick={async () => {selectedFile = file}}>
                                    <p>{getFileName(file)}</p>
                                </div>
                                <!-- svelte-ignore a11y_click_events_have_key_events -->
                                <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                                <p class='text-2xl text-slate-400 hover:text-red-500' onclick={() => {removeRecentFolder(file)}}>&times;</p>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>

            <!--Folders and files-->
            <div class='flex flex-col w-4/5'>
                <!-- top bar -->
                <div class='h-10 w-full flex justify-between p-1 items-center border-b border-slate-500'>
                    <div class='flex overflow-hidden text-xs'>
                        <button class='bg-slate-300 text-black px-1 mr-2 my-1' onclick={goToParentDir}>&uarr;</button>
                        <!-- path -->
                        <div id='dialog-path-breakdown' class='flex items-center h-10 mr-6'>
                            {#each pathBreakdown as dir, i}
                                <!-- svelte-ignore a11y_click_events_have_key_events -->
                                <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                                <p class='cursor-pointer hover:text-sky-300' onclick={() =>{populateDirList(pathBreakdown.slice(0, i+1).join(sep()))}}>{dir}</p>
                                {#if i != pathBreakdown.length - 1}
                                    <p class='cursor-default mx-1'>/</p>
                                {/if}
                            {/each}
                        </div>
                    </div>
                    <input type="text" bind:this={searchBar} oninput={searchBarInput} placeholder="Search..." class='border border-slate-500 w-1/4 px-2 rounded-lg focus:border-slate-500'>
                </div>
                <div class='flex justify-between px-4 pt-1'>
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                    <p class='cursor-pointer hover:text-sky-300' onclick={() => {dialogListOrder.orderBy = 'name'; dialogListOrder.descending = !dialogListOrder.descending; populateDirList(dialogCurrentPath)}}>Name</p>
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                    <p class='cursor-pointer hover:text-sky-300' onclick={() => {dialogListOrder.orderBy = 'date'; dialogListOrder.descending = !dialogListOrder.descending; populateDirList(dialogCurrentPath)}}>Date modified</p>
                </div>
                <!-- list of folders and files -->
                 {#if !selectDrive}
                    <div class='overflow-auto flex-auto'>
                        <div class='p-1 overflow-auto'>
                            {#each dialogList as item}
                            <!-- svelte-ignore a11y_click_events_have_key_events -->
                            <!-- svelte-ignore a11y_no_static_element_interactions -->
                            <div class='flex justify-between px-2 py-1 cursor-pointer hover:bg-slate-600' onclick={async () => {item.isDir ? populateDirList(await join(dialogCurrentPath, item.name)) : selectedFile = await join(dialogCurrentPath, item.name)}}>
                                <div class='flex'>
                                    <img src={item.isDir ? folder_icon_url : file_icon_url} alt='' class='h-6 w-6 mr-2'>
                                    <p class='text-slate-300'>{item.name}</p>
                                </div>
                                <p class='text-slate-300'>{item.mtime != null ? formatTime(item.mtime) : ''}</p>
                            </div>
                            {/each}
                        </div>
                    </div>
                    <div class='p-2 flex items-center'>
                        <input bind:value={newFolderName} type="text" placeholder="New folder name" class='border border-slate-500 px-2 py-1 rounded-lg focus:border-slate-500'>
                        <button class='mx-2 text-black text-xs bg-slate-300' onclick={() => {createNewFolder(newFolderName)}}>Create new folder</button>
                        <p class='text-red-600'>{message}</p>
                    </div>
                {:else}
                    <div class='p-2 flex items-center'>
                        <input type="text" bind:this={driveInput} placeholder='Drive name e.g. "C" or "D"' class='border border-slate-500 px-2 rounded-lg focus:border-slate-500'>
                        <button onclick={goToDrive} class='mx-2'>Go to drive</button>
                        <p class='text-red-600'>{driveMessage}</p>
                    </div>
                {/if}
            </div>
        </div>

        <!--Footer-->
        <div class='border-t border-slate-500 py-2 px-4 flex items-center justify-between'>
            <div class='w-3/4'>
                <p class='text-slate-400 truncate text-sm'>{selectedFile}</p>
            </div>
            <div class='flex'>
                <button onclick={close} class='border-2 bg-transparent bg-none border-rose-500 text-rose-500 hover:border-rose-700 hover:text-rose-700 hover:bg-none text-sm'>Cancel</button>
                <button class='mx-2 border-2 bg-transparent bg-none border-sky-300 text-sky-300 hover:border-sky-500 hover:text-sky-500 hover:bg-none text-sm' onclick={setFile}>Select</button>
            </div>
        </div>
    </div>
</div>
{/if}

<style>
    #modal {
        position: fixed;
        top: 0;
        bottom: 0;
        right: 0;
        left: 0;
        display: flex;
        justify-content: center;
        align-items: center;

    }

    #contents{
        pointer-events: auto;
    }

    #dialog-path-breakdown{
        flex: 1;
        display: flex;
        align-items: center;
        overflow-y: hidden;
        overflow-x: auto;
        white-space: nowrap;
    }

    @layer base{

        button{
            padding: 0.3rem 0.7rem;
        }
    }
</style>