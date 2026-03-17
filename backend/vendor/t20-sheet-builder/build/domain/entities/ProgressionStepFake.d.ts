import type { BuildStepInterface } from './BuildStep';
import { type SerializedSheetBuildStep } from './Sheet';
import type { ActionInterface, ActionType } from './Sheet/SheetActions';
export declare class ProgressionStepFake<T extends ActionType> implements BuildStepInterface<T> {
    readonly action: ActionInterface<T>;
    readonly description: string;
    constructor(action: ActionInterface<T>);
    serialize(): SerializedSheetBuildStep;
}
