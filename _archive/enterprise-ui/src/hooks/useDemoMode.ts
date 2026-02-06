// Jorge's Demo Mode React Hook
// Centralized state management for professional demonstration system

import { useState, useCallback, useEffect } from 'react';
import { scenarioEngine, type DemoScenario, type ConversationStep } from '@/lib/demo/ScenarioEngine';
import { conversationSimulator, type SimulationSettings, type ConversationState } from '@/lib/demo/ConversationSimulator';
import { demoDataGenerator, type SyntheticProperty, type SyntheticLead } from '@/lib/demo/DemoDataGenerator';

export interface DemoModeState {
  // Core state
  isActive: boolean;
  currentScenario: DemoScenario | null;
  availableScenarios: DemoScenario[];

  // Conversation state
  conversationState: ConversationState;
  currentStep: ConversationStep | null;

  // Demo data
  demoProperties: SyntheticProperty[];
  demoLeads: SyntheticLead[];

  // Presentation state
  isPresentationMode: boolean;
  isFullScreen: boolean;

  // Settings
  simulationSettings: SimulationSettings;

  // Progress
  scenarioProgress: number;
  conversationProgress: number;

  // Error handling
  error: string | null;
  isLoading: boolean;
}

export interface DemoModeActions {
  // Scenario management
  loadScenario: (scenarioId: string) => Promise<void>;
  startDemo: () => void;
  pauseDemo: () => void;
  resetDemo: () => void;

  // Step control
  nextStep: () => void;
  previousStep: () => void;
  jumpToStep: (stepNumber: number) => void;
  skipTyping: () => void;

  // Presentation mode
  enterPresentationMode: () => void;
  exitPresentationMode: () => void;
  toggleFullScreen: () => void;

  // Settings
  updateSimulationSettings: (settings: Partial<SimulationSettings>) => void;

  // Data generation
  refreshDemoData: () => void;
  generateCustomScenario: (config: any) => DemoScenario;

  // Export functionality
  exportTranscript: () => string;
  exportScenarioData: () => any;
}

export function useDemoMode(): [DemoModeState, DemoModeActions] {
  // Core state
  const [state, setState] = useState<DemoModeState>({
    isActive: false,
    currentScenario: null,
    availableScenarios: [],
    conversationState: conversationSimulator.getState(),
    currentStep: null,
    demoProperties: [],
    demoLeads: [],
    isPresentationMode: false,
    isFullScreen: false,
    simulationSettings: {
      typingSpeed: 'realistic',
      includeTypingIndicators: true,
      autoAdvance: false,
      pauseBetweenMessages: 1500,
      enableInterruptions: true,
      showConfidence: true,
      displayReasoning: false
    },
    scenarioProgress: 0,
    conversationProgress: 0,
    error: null,
    isLoading: false
  });

  // Initialize demo system
  useEffect(() => {
    const initializeDemo = async () => {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      try {
        // Load available scenarios
        const scenarios = scenarioEngine.getAvailableScenarios();

        // Generate demo data
        const dataset = demoDataGenerator.generateCompleteDataset();

        // Setup conversation simulator callbacks
        conversationSimulator.setCallbacks({
          onMessageStart: (step) => {
            setState(prev => ({ ...prev, currentStep: step }));
          },
          onMessageComplete: (step) => {
            updateProgress();
          },
          onTypingUpdate: (text) => {
            // Handle typing updates if needed
          },
          onStepComplete: (step) => {
            updateProgress();
          },
          onScenarioComplete: () => {
            setState(prev => ({
              ...prev,
              isActive: false,
              scenarioProgress: 100,
              conversationProgress: 100
            }));
          }
        });

        setState(prev => ({
          ...prev,
          availableScenarios: scenarios,
          demoProperties: dataset.properties,
          demoLeads: dataset.leads,
          isLoading: false
        }));

      } catch (error) {
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Failed to initialize demo system',
          isLoading: false
        }));
      }
    };

    initializeDemo();
  }, []);

  // Update progress
  const updateProgress = useCallback(() => {
    const conversationProgress = conversationSimulator.getProgress();
    const scenarioProgress = scenarioEngine.getProgress();

    setState(prev => ({
      ...prev,
      conversationProgress: conversationProgress.percentage,
      scenarioProgress,
      conversationState: conversationSimulator.getState()
    }));
  }, []);

  // Load and start a scenario
  const loadScenario = useCallback(async (scenarioId: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const scenario = scenarioEngine.startScenario(scenarioId);
      const currentStep = scenarioEngine.getCurrentStep();

      setState(prev => ({
        ...prev,
        currentScenario: scenario,
        currentStep,
        isLoading: false,
        scenarioProgress: 0,
        conversationProgress: 0
      }));

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to load scenario',
        isLoading: false
      }));
    }
  }, []);

  // Start demo
  const startDemo = useCallback(() => {
    if (!state.currentScenario) {
      setState(prev => ({ ...prev, error: 'No scenario loaded' }));
      return;
    }

    conversationSimulator.startConversation(
      state.currentScenario.conversationFlow,
      state.simulationSettings
    );

    setState(prev => ({
      ...prev,
      isActive: true,
      error: null,
      conversationState: conversationSimulator.getState()
    }));
  }, [state.currentScenario, state.simulationSettings]);

  // Pause demo
  const pauseDemo = useCallback(() => {
    conversationSimulator.pauseConversation();
    setState(prev => ({
      ...prev,
      isActive: false,
      conversationState: conversationSimulator.getState()
    }));
  }, []);

  // Reset demo
  const resetDemo = useCallback(() => {
    conversationSimulator.resetConversation();
    scenarioEngine.resetScenario();

    setState(prev => ({
      ...prev,
      isActive: false,
      currentStep: scenarioEngine.getCurrentStep(),
      scenarioProgress: 0,
      conversationProgress: 0,
      conversationState: conversationSimulator.getState()
    }));
  }, []);

  // Step controls
  const nextStep = useCallback(() => {
    conversationSimulator.nextStep();
    const nextScenarioStep = scenarioEngine.nextStep();

    setState(prev => ({
      ...prev,
      currentStep: nextScenarioStep,
      conversationState: conversationSimulator.getState()
    }));

    updateProgress();
  }, [updateProgress]);

  const previousStep = useCallback(() => {
    // Note: This would require implementing reverse functionality in engines
    setState(prev => ({ ...prev, error: 'Previous step not yet implemented' }));
  }, []);

  const jumpToStep = useCallback((stepNumber: number) => {
    const targetStep = scenarioEngine.jumpToStep(stepNumber);
    setState(prev => ({
      ...prev,
      currentStep: targetStep
    }));
    updateProgress();
  }, [updateProgress]);

  const skipTyping = useCallback(() => {
    conversationSimulator.skipTyping();
  }, []);

  // Presentation mode controls
  const enterPresentationMode = useCallback(() => {
    setState(prev => ({ ...prev, isPresentationMode: true }));
  }, []);

  const exitPresentationMode = useCallback(() => {
    setState(prev => ({ ...prev, isPresentationMode: false, isFullScreen: false }));
  }, []);

  const toggleFullScreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setState(prev => ({ ...prev, isFullScreen: true }));
      });
    } else {
      document.exitFullscreen().then(() => {
        setState(prev => ({ ...prev, isFullScreen: false }));
      });
    }
  }, []);

  // Settings
  const updateSimulationSettings = useCallback((newSettings: Partial<SimulationSettings>) => {
    const updatedSettings = { ...state.simulationSettings, ...newSettings };
    conversationSimulator.updateSettings(updatedSettings);

    setState(prev => ({
      ...prev,
      simulationSettings: updatedSettings
    }));
  }, [state.simulationSettings]);

  // Data generation
  const refreshDemoData = useCallback(() => {
    const dataset = demoDataGenerator.generateCompleteDataset();
    setState(prev => ({
      ...prev,
      demoProperties: dataset.properties,
      demoLeads: dataset.leads
    }));
  }, []);

  const generateCustomScenario = useCallback((config: any): DemoScenario => {
    // This would be implemented to create custom scenarios
    throw new Error('Custom scenario generation not yet implemented');
  }, []);

  // Export functionality
  const exportTranscript = useCallback(() => {
    return conversationSimulator.exportTranscript();
  }, []);

  const exportScenarioData = useCallback(() => {
    return {
      scenario: state.currentScenario,
      progress: state.scenarioProgress,
      completedSteps: state.conversationState.completedSteps,
      demoData: {
        properties: state.demoProperties,
        leads: state.demoLeads
      },
      settings: state.simulationSettings,
      timestamp: new Date().toISOString()
    };
  }, [state]);

  // Actions object
  const actions: DemoModeActions = {
    loadScenario,
    startDemo,
    pauseDemo,
    resetDemo,
    nextStep,
    previousStep,
    jumpToStep,
    skipTyping,
    enterPresentationMode,
    exitPresentationMode,
    toggleFullScreen,
    updateSimulationSettings,
    refreshDemoData,
    generateCustomScenario,
    exportTranscript,
    exportScenarioData
  };

  return [state, actions];
}

// Utility hooks for specific demo aspects
export function useScenarioSelection() {
  const [demoState] = useDemoMode();

  return {
    scenarios: demoState.availableScenarios,
    categorized: {
      seller_qualification: demoState.availableScenarios.filter(s => s.category === 'seller_qualification'),
      buyer_nurture: demoState.availableScenarios.filter(s => s.category === 'buyer_nurture'),
      market_intelligence: demoState.availableScenarios.filter(s => s.category === 'market_intelligence'),
      cross_bot_coordination: demoState.availableScenarios.filter(s => s.category === 'cross_bot_coordination')
    }
  };
}

export function usePresentationControls() {
  const [demoState, actions] = useDemoMode();

  return {
    isPresentationMode: demoState.isPresentationMode,
    isFullScreen: demoState.isFullScreen,
    isActive: demoState.isActive,
    progress: demoState.scenarioProgress,
    controls: {
      start: actions.startDemo,
      pause: actions.pauseDemo,
      reset: actions.resetDemo,
      next: actions.nextStep,
      skip: actions.skipTyping,
      fullScreen: actions.toggleFullScreen,
      presentationMode: actions.enterPresentationMode,
      exit: actions.exitPresentationMode
    }
  };
}

export function useConversationDisplay() {
  const [demoState] = useDemoMode();

  return {
    currentStep: demoState.currentStep,
    conversationState: demoState.conversationState,
    isTyping: demoState.conversationState.isTyping,
    completedSteps: demoState.conversationState.completedSteps,
    settings: demoState.simulationSettings
  };
}

export default useDemoMode;