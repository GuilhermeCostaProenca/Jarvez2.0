export type SerializedCritical = {
    threat: number;
    multiplier: number;
};
export declare class Critical {
    readonly threat: number;
    readonly multiplier: number;
    constructor(threat?: number, multiplier?: number);
    serialize(): SerializedCritical;
    private validateThreat;
    private validateMultiplier;
}
