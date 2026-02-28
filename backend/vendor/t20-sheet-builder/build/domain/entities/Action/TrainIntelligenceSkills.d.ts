import { Action, type ActionSubClassParams } from './Action';
export declare class TrainIntelligenceSkills extends Action<'trainIntelligenceSkills'> {
    constructor(params: ActionSubClassParams<'trainIntelligenceSkills'>);
    execute(): void;
    getDescription(): string;
}
