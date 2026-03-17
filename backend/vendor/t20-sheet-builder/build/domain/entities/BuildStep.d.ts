import { type SerializedSheetBuildStep } from './Sheet/SerializedSheet/SerializedSheetInterface';
import type { ActionInterface, ActionType } from './Sheet/SheetActions';
export type BuildStepInterface<T extends ActionType = ActionType> = {
    action: ActionInterface<T>;
    serialize(): SerializedSheetBuildStep;
};
export declare class BuildStep<T extends ActionType = ActionType> implements BuildStepInterface<T> {
    readonly action: ActionInterface<T>;
    constructor(action: ActionInterface<T>);
    serialize(): SerializedSheetBuildStep;
}
