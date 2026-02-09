function vflux_post(output)
%
% vlux_post - post-calculation component of VFLUX program, optionally
%             called by vflux.m
%
% Description:
% Runs results visualization, ideal sensor spacing statistics, and
% sensitivity analysis routines on the results from a VFLUX run.
%
% Usage:
%   vflux_post(vflux_output)
%
% Input:
%   vflux_output = the MATLAB structure created by a successful run of vflux.m

% Written by Ryan Gordon, Syracuse University, October 2011
%   Department of Earth Sciences
%   204 Heroy Geology Lab
%   Syracuse, NY  13244
%   Contact: rpgordon@syr.edu
% Copyright (c) 2011, Ryan P. Gordon. All rights reserved.
% Revision: 103, updated 06/11/2014  %+  Revision number was 102 - Dylan

%Plot time series and flux results
disp(' ')
disp('Would you like to plot flux and thermal diffusivity results?') %+
answer=input('Enter 1 for Yes, or press ENTER for No: ');
if answer
    disp(' ')
    res=input(' Please enter your temperature sensors'' precision in\n degrees C, or press ENTER to leave blank: '); %get sensor resolution
    figure %create time series results figure
    set(gcf, 'Position', get(0,'Screensize')); %maximize figure window
    subplot(2,2,1) %create first subplot in 2x2 matrix 
    plot(output.time,output.temp) %plot raw time series
    set(gca,'XLim',[output.time(1),output.time(end)]) %set x-axis limits to time range
    title('Raw Time Series'), xlabel('time (days)'), ylabel('temperature (oC)')
    splot=subplot(2,2,2); %save subplot ID as splot for use in drawing line on amplitude plot, below
    plot(output.dtime,output.ftemp) %plot filtered time series
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
    title('Filtered Time Series'), xlabel('time (days)'), ylabel('temperature (oC)')
    leg=legend(num2str(output.depth')); %creates legend of sensor depths
    %set(get(leg,'title'),'string','Sensor Depth (m)'); %gives legend a title
    pos=get(leg,'position'); set(leg,'position',[pos(1)+1.1*pos(3),pos(2),pos(3),pos(4)]); %shifts legend to the right, outside of axis box
    subplot(2,2,3)
    hold on %hold plot
    if ~isempty(res) %if resolution value was entered
        hline=line(get(splot,'xlim'),[res res],'Color','r','LineWidth',2); %plot horz line on amplitude plot at sensor resolution
        legend('sensor precision') %add sensor resolution line to the legend
    else hline=[]; %necessary for set 'Children' command below
    end %if
    hplot=plot(output.dtime,output.amp); %plot amplitudes
    hold off
    box on %for some reason, using hold turns the box off -MATLAB bug?
    set(gca,'Children',[hline; hplot]) %reorder the plot so line is on top
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
    ylim=get(gca,'YLim'); set(gca,'YLim',[0 ylim(2)]) %start y-axis at zero
    title('Amplitudes'), xlabel('time (days)'), ylabel('temperature (oC)')
    subplot(2,2,4)
    plot(output.dtime,output.phs) %plot phases
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
    title('Phase Angles'), xlabel('time (days)'), ylabel('phase (rad)')
    disp(' Pause for plot: press any key to continue.'), pause %pause for plot
    
    figure %create flux results figure 
    set(gcf, 'Position', get(0,'Screensize')); %maximize figure window
    subplot(3,2,1) %create first subplot in 3x2 matrix
    plot(output.dtime,output.fluxha) %plot Hatch amp flux
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
    title('Flux (Hatch Amplitude)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
    subplot(3,2,2)
    plot(output.dtime,output.fluxhp) %plot Hatch phase flux
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
    title('Flux (Hatch Phase)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
    leg=legend(num2str(output.fluxinfo(4,:)')); %creates legend of center-of-pair depths
    %set(get(leg,'title'),'string','Center-of-Pair Depth (m)'); %gives legend a title
    pos=get(leg,'position'); set(leg,'position',[pos(1)+1.1*pos(3),pos(2),pos(3),pos(4)]); %shifts legend to the right, outside of axis box
    subplot(3,2,3)
    plot(output.dtime,output.fluxka) %plot Keery amp flux
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
    title('Flux (Keery Amplitude)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
    subplot(3,2,4)
    plot(output.dtime,output.fluxkp) %plot Keery phase flux
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range
    title('Flux (Keery Phase)'), xlabel('time (days)'), ylabel('downward flux (m/s)')
    subplot(3,2,5)
    plot(output.dtime,output.fluxm) %plot McCallum flux                                 %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    title('Flux (McCallum)'), xlabel('time (days)'), ylabel('downward flux (m/s)')          %+
    subplot(3,2,6)
    plot(output.dtime,output.fluxl) %plot Luce flux
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    title('Flux (Luce)'), xlabel('time (days)'), ylabel('downward flux (m/s)')              %+
    disp(' Pause for plot: press any key to continue.'), pause %pause for plot              %+
    
    figure % create figure for McCallum and Luce methods (for both flux and thermal diffusivity, with thermal diffusivity from user inputs, and theoretical limits also displayed %+
    set(gcf, 'Position', get(0,'Screensize')); %maximize figure window                      %+
    subplot(2,2,1) %create first subplot in 2x2 matrix                                      %+
    plot(output.dtime,output.fluxm) %plot McCallum flux                                 %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+ 
    title('Flux (McCallum)'), xlabel('time (days)'), ylabel('downward flux (m/s)')          %+
    leg=legend(num2str(output.fluxinfo(4,:)')); %creates legend of center-of-pair depths
    %set(get(leg,'title'),'string',' Flux (m/s) at Depth (m)'); %gives legend a title
    pos=get(leg,'position'); set(leg,'position',[pos(1)+1.1*pos(3),pos(2),pos(3),pos(4)]); %shifts legend to the right, outside of axis box       
    subplot(2,2,2) %plot McCallum Ke                                                        %+
    plot(output.dtime,output.Kem) %plot McCallum thermal diffusivity                        %+ 
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[cell2mat(output.parameters(4,8))/10000 , cell2mat(output.parameters(4,8))/10000], '-') %+ 
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[2.08E-06 , 2.07882E-06 ], 'r--')                %+    
    hold on                                                                                 %+                                                                               %+                                                                                         %+
    plot([output.dtime(1),output.dtime(end)],[2.61E-07 ,2.61E-07 ], 'r--')                    %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    set(gca,'YLim',[0.0,3.0E-6 ]) %set y-axis limits to time range Arbitratily set          %+ 
    title('Thermal diffusivity (McCallum)'), xlabel('time (days)'), ylabel('Thermal diffusivity (m{^2}/s)')     %+   
    labels1 = cellstr(['User input       ';'Theoretical limit']); % for lines of Ke plots
    labels2 = cellstr(num2str(output.fluxinfo(4,:)'));  % Ke for all sensor pairs    
    labels3 = cat(1,labels2,labels1);  % combine labels for the legend 
    leg=legend(labels3);                                                     %----
    %set(get(leg,'title'),'string','Therm. Diff. (m^{2}/s) at Depth (m)'); %gives legend a title                          %+ 
    pos=get(leg,'position'); set(leg,'position',[pos(1)+1.1*pos(3),pos(2),pos(3),pos(4)]); %shifts legend to the right, outside of axis box   %+
    
    subplot(2,2,3) %plot Luce flux                                                          %+
    plot(output.dtime,output.fluxl) %plot Luce flux                                     %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    title('Flux (Luce)'), xlabel('time (days)'), ylabel('downward flux (m/s)')              %+
    subplot(2,2,4) %plot Luce Ke                                                            %+ 
    plot(output.dtime,output.Kem) %plot McCallum flux                                   %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    title('Thermal diffusivity (Luce)'), xlabel('time (days)'), ylabel('downward flux (m{^2}/s)')   %+     
    
    subplot(2,2,4) %plot Luce     Ke                                                        %+
    plot(output.dtime,output.Kel) %plot Luce Ke                                         %+ 
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[cell2mat(output.parameters(4,8))/10000 , cell2mat(output.parameters(4,8))/10000], '-') %+ 
    hold on                                                                                 %+                                                                            %+        
    plot([output.dtime(1),output.dtime(end)],[2.07882E-06 , 2.07882E-06 ], 'r--')                %+
    hold on                                                                                 %+                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[2.61E-07 ,2.61E-07 ], 'r--')                    %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    set(gca,'YLim',[0.0,3.0E-6 ]) %set y-axis limits to time range Arbitratily set          %+ 
    title('Thermal diffusivity (Luce)'), xlabel('time (days)'), ylabel('Thermal diffusivity (m{^2}/s)')     %+
    disp(' Pause for plot: press any key to continue.'), pause %pause for plot              %+    
end %if

% Refine range of plausible Ke values %+
disp(' ')%+
disp('Would you like to refine the range of plausible thermal diffusivity for the McCallum/ Luce plots?')%+
answer=input('Enter 1 for Yes, or press ENTER for No: ');%+
if answer %+
    disp('Using units of J, °C, m, kg and s, enter the range in thermal properties when promted: ')%+
    disp(' ')%+
    disp('Enter range of porosity (-) below (typical range 0.2 - 0.5)')%+
    poro_l = input('lower: ');%+
    poro_u = input('upper: ');%+
    disp(' ')%+
    disp('Enter range of solid density(kg/m^3, typical range 2625 - 2680)')%+
    ps_l = input('lower: ');%+
    ps_u = input('upper: ');%+
    disp(' ')%+
    disp('Enter range of solid specific heat capacity (J/kg/°C, typical range 731 - 1078)')%+
    cs_l = input('lower: ');%+
    cs_u = input('upper: ');%+
    disp(' ')%+
    disp('Enter range of solid thermal conductivity (W/m/°C, typical range 2.18 - 8.39)')%+
    ks_l = input('lower: ');%+
    ks_u = input('upper: ');%+

    % properties of water (fixed)%+
    pw = 1000.0;%+
    kw = 0.6;%+
    cw = 4186.0;%+

    % calculate upper and lower values%+
    Ke_u = ((kw^poro_l)*(ks_u^(1.0-poro_l))) /( (poro_l*cw*pw)+((1.0-poro_l)*cs_l*ps_l) );%+
    Ke_l = ((kw^poro_u)*(ks_l^(1.0-poro_u))) /(  (poro_u*cw*pw)+((1.0-poro_u)*cs_u*ps_u) ); %+

    figure % create figure for McCallum and Luce methods (for both flux and thermal diffusivity, with thermal diffusivity from user inputs, and theoretical limits also displayed %+
    set(gcf, 'Position', get(0,'Screensize')); %maximize figure window                      %+
    subplot(2,2,1) %create first subplot in 2x2 matrix                                      %+
    plot(output.dtime,output.fluxm) %plot McCallum flux                                 %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+ 
    title('Flux (McCallum)'), xlabel('time (days)'), ylabel('downward flux (m/s)')          %+
    leg=legend(num2str(output.fluxinfo(4,:)')); %creates legend of center-of-pair depths
    %set(get(leg,'title'),'string',' Flux (m/s) at Depth (m)'); %gives legend a title
    pos=get(leg,'position'); set(leg,'position',[pos(1)+1.1*pos(3),pos(2),pos(3),pos(4)]); %shifts legend to the right, outside of axis box       
    subplot(2,2,2) %plot McCallum Ke                                                        %+
    plot(output.dtime,output.Kem) %plot McCallum flux                                   %+ 
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[cell2mat(output.parameters(4,8))/10000 , cell2mat(output.parameters(4,8))/10000], '-') %+ 
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[Ke_u,Ke_u], 'k--') %+   
    hold on 
    plot([output.dtime(1),output.dtime(end)],[2.07882E-06 , 2.07882E-06  ], 'r--')                %+    
    hold on                                                                                 %+                                                                               %+        
    plot([output.dtime(1),output.dtime(end)],[Ke_l,Ke_l], 'k--') %+     
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[2.61E-07 ,2.61E-07], 'r--')                    %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    set(gca,'YLim',[0.0,3.0E-6 ]) %set y-axis limits to time range Arbitratily set          %+ 
    title('Thermal diffusivity (McCallum)'), xlabel('time (days)'), ylabel('Thermal diffusivity (m{^2}/s)')     %+   
    labels1 = cellstr(['User input       ';'Refined limit    ';'Theoretical limit']); % for lines of Ke plots
    labels2 = cellstr(num2str(output.fluxinfo(4,:)'));  % Ke for all sensor pairs    
    labels3 = cat(1,labels2,labels1);  % combine labels for the legend
    leg=legend(labels3);                                                     %----
    %set(get(leg,'title'),'string','Therm. Diff. (m^{2}/s) at Depth (m)'); %gives legend a title                          %+ 
    pos=get(leg,'position'); set(leg,'position',[pos(1)+1.1*pos(3),pos(2),pos(3),pos(4)]); %shifts legend to the right, outside of axis box   %+
    
    subplot(2,2,3) %plot Luce flux                                                          %+
    plot(output.dtime,output.fluxl) %plot Luce flux                                     %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    title('Flux (Luce)'), xlabel('time (days)'), ylabel('downward flux (m/s)')              %+
    subplot(2,2,4) %plot Luce Ke                                                            %+ 
    plot(output.dtime,output.Kem) %plot McCallum flux                                   %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    title('Thermal diffusivity (Luce)'), xlabel('time (days)'), ylabel('downward flux (m{^2}/s)')   %+     
    
    subplot(2,2,4) %plot Luce     Ke                                                        %+
    plot(output.dtime,output.Kel) %plot Luce Ke                                         %+ 
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[cell2mat(output.parameters(4,8))/10000 , cell2mat(output.parameters(4,8))/10000], '-') %+ 
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[Ke_u,Ke_u], 'k--') %+  
    hold on                                                                                 %+        
    plot([output.dtime(1),output.dtime(end)],[2.07882E-06 , 2.07882E-06  ], 'r--')                %+
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[Ke_l,Ke_l], 'k--') %+        
    hold on                                                                                 %+
    plot([output.dtime(1),output.dtime(end)],[2.61E-07 ,2.61E-07 ], 'r--')                    %+
    set(gca,'XLim',[output.dtime(1),output.dtime(end)]) %set x-axis limits to time range    %+
    set(gca,'YLim',[0.0,3.0E-6 ]) %set y-axis limits to time range Arbitratily set          %+ 
    title('Thermal diffusivity (Luce)'), xlabel('time (days)'), ylabel('Thermal diffusivity (m{^2}/s)')     %+
    disp(' Pause for plot: press any key to continue.'), pause %pause for plot              %+    
end %while

% Plot sensor spacing statistics
disp(' ')
disp('Would you like to view sensor spacing statistics?')
answer=input('Enter 1 for Yes, or press ENTER for No: ');
while answer
    disp(' ')
    disp(' View sensor spacing statistics for which method?')
    disp('   1) Hatch Amplitude')
    disp('   2) Keery Amplitude')
    disp('   3) Hatch Phase')
    disp('   4) Keery Phase')
    disp('   5) McCallum')  
    disp('   6) Luce')      
    method=input(' Select a menu number, or ENTER to exit: ');
    if isempty(method), break %break out of while loop if 'Exit' is chosen
    elseif method~=1 && method~=2 && method~=3 && method~=4 && method~=5 && method~=6,  continue %re-ask question if anything else is entered
    end %if
    
    windows=output.fluxinfo(1,:); %get first row of fluxinfo (windows of all calculations done)
    uwindows=unique(windows); %get unique window values
    uwindows=sort(uwindows); %sorts uwindows in ascending order

    figure %create figure (will have 2x3 subplots)
    set(gcf, 'Position', get(0,'Screensize')); %maximize figure window
    
    for i=1:length(uwindows)
        cols=find(windows==uwindows(i)); %column numbers in fluxinfo or fluxha, etc., that apply to window number "i"
        switch method
            case 1
                methods='Hatch Amplitude Method';
                numnans=sum(isnan(output.fluxha(1:end-1,cols))); %number of NaN's (same in other cases, below).  Excludes last line, which is usually NaN's.
                numfin=sum(isfinite(output.fluxha(1:end-1,cols))); %number of finite numbers (non-NaN's) (same in other cases, below).  Also excludes last line.
            case 2
                methods='Keery Amplitude Method';
                numnans=sum(isnan(output.fluxka(1:end-1,cols)));
                numfin=sum(isfinite(output.fluxka(1:end-1,cols)));
            case 3
                methods='Hatch Phase Method';
                numnans=sum(isnan(output.fluxhp(1:end-1,cols)));
                numfin=sum(isfinite(output.fluxhp(1:end-1,cols)));
            case 4
                methods='Keery Phase Method';
                numnans=sum(isnan(output.fluxkp(1:end-1,cols)));
                numfin=sum(isfinite(output.fluxkp(1:end-1,cols)));
            case 5
                methods='McCallum Method';
                numnans=sum(isnan(output.fluxm(1:end-1,cols)));
                numfin=sum(isfinite(output.fluxm(1:end-1,cols))); 
            case 6
                methods='Luce Method';
                numnans=sum(isnan(output.fluxl(1:end-1,cols)));
                numfin=sum(isfinite(output.fluxl(1:end-1,cols)));                 
        end %switch
        pctok=numfin./(numnans+numfin)*100; %percent of calculations that are not NaN (ie, "ok"), excluding last line
                
        if i<7 %if 6 or fewer unique windows have been plotted (ie still on first figure window)
            j=i; %j is index for subplot number in figure (see subplot command below), here equal to i
        elseif rem(i,7)==0 %if i is evenly divisable by 7 (ie, we're on the first plot in a 6-plot figure window)
            disp(' Pause for plot: press any key to continue.'), pause %pause for plot
            figure %create new figure window
            set(gcf, 'Position', get(0,'Screensize')); %maximize figure windows
            j=1; %reset j
        else
            j=j+1; %advance j
        end %if
        subplot(2,3,j) %create j-th subplot in 2x3 matrix
        copdepths=output.fluxinfo(4,cols); %center-of-pair depths
        bar(copdepths,pctok,0.8) %create bar plot
        set(gca,'YLim',[0 105]) %y-axis from 0 to 105
        set(gca,'XTick',copdepths) %set the x-axis ticks to center of pair depths only
        title(sprintf('window=%d',uwindows(i))), xlabel('center-of-pair depth (m)'), ylabel('percent of flux values successfully calculated')
        if i==1, xlim=get(gca,'XLim'); end %get x-axis limits for first plot
        set(gca,'XLim',xlim) %set xlim for all plots
    end %for
    disp(' Pause for plot: Press any key to continue.'), pause
end %while

end %function
% 
% Copyright (c) 2011, Ryan P. Gordon.
% All rights reserved.
% 
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are
% met:
% (1) Redistributions of source code must retain the above copyright
% notice, this list of conditions and the following disclaimer.
% (2) Redistributions in binary form must reproduce the above copyright
% notice, this list of conditions and the following disclaimer in the
% documentation and/or other materials provided with the distribution.
% 
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
% IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
% THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
% PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
% CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
% EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
% PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
% PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
% LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
% NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
% SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.